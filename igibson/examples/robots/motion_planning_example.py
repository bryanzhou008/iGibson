import argparse
import logging
import os
import sys
from sys import platform

import numpy as np
import yaml

import igibson
from igibson import object_states
from igibson.envs.igibson_env import iGibsonEnv
from igibson.utils.constants import ViewerMode
from igibson.utils.motion_planning_utils import MotionPlanner
from igibson.utils.motion_planning_wrapper import MotionPlanningWrapper


def print_mp_info():
    """
    Prints out useful information for user for knowing how to use this MP demo
    """

    def print_command(char, info):
        char += " " * (10 - len(char))
        print("{}\t{}".format(char, info))

    print()
    print("*" * 30)
    print("MOTION PLANNING DEMO")
    print("*" * 30)
    print()
    print("Use your mouse to generate and execute motion plans:")
    print()
    print_command(
        "Left click",
        "Create (click), visualize (drag) and plan / execute (release) a base motion subgoal "
        "for the robot base to reach the physical point that corresponds to the clicked pixel",
    )
    print_command(
        "Middle click",
        "Create, and plan / execute an arm motion subgoal for the robot end-effector "
        "to reach the physical point that corresponds to the clicked pixel",
    )
    print()
    print("Press 'm' to toggle between viewer modes:")
    print()
    print_command("Nav mode", "Enables direct robot navigation and movement of viewer camera")
    print_command("Manip mode", "Enables direct manipulation of objects within the scene")
    print_command("Planning mode", "Enables generation and execution of motion plans (default)")
    print()
    print("Press 'h' for on-screen help.")
    print()
    print("*" * 30)


def run_example(config, programmatic_actions, headless, short_exec):
    config_filename = config
    config_data = yaml.load(open(config_filename, "r"), Loader=yaml.FullLoader)
    # Reduce texture scale for Mac.
    if platform == "darwin":
        config_data["texture_scale"] = 0.5
    config_data["load_object_categories"] = [
        "bottom_cabinet"
    ]  # Uncomment this line to accelerate loading with only the building
    config_data["load_room_types"] = ["living_room"]
    config_data["hide_robot"] = False
    env = iGibsonEnv(
        config_file=config_data,
        mode="gui_interactive" if not headless else "headless",
        action_timestep=1.0 / 120.0,
        physics_timestep=1.0 / 120.0,
    )

    full_observability_2d_planning = True
    collision_with_pb_2d_planning = False
    motion_planner = MotionPlanner(
        env,
        optimize_iter=10,
        full_observability_2d_planning=full_observability_2d_planning,
        collision_with_pb_2d_planning=collision_with_pb_2d_planning,
        visualize_2d_planning=False,  # not headless,
        visualize_2d_result=not headless,
    )
    state = env.reset()

    for obj in env.scene.get_objects():
        if obj.category == "bottom_cabinet":
            obj.states[object_states.Open].set_value(True)

    if programmatic_actions or headless:

        if not headless:
            # Set viewer camera and directly set mode to planning mode
            env.simulator.viewer.initial_pos = [-0.8, 0.7, 1.7]
            env.simulator.viewer.initial_view_direction = [0.1, -0.9, -0.5]
            env.simulator.viewer.reset_viewer()

        env.land(env.robots[0], [0, 0, 0], [0, 0, 0])
        env.robots[0].tuck()
        if full_observability_2d_planning and not collision_with_pb_2d_planning:  # Only hard for the full map
            base_pose1 = [-2.98253920783756465, -1.344157042454841, 1.9658493926322262]
        else:
            base_pose1 = [0.48253920783756465, -1.344157042454841, 1.9658493926322262]

        max_attempts = 10

        # If we use this flag, the robot navigates in front of the cupboard (easy) to prepare for an arm planning task
        testing_arm_planning = True

        if not testing_arm_planning:
            for attempt in range(1, max_attempts + 1):
                plan = motion_planner.plan_base_motion(base_pose1)
                if plan is not None and len(plan) > 0:
                    motion_planner.dry_run_base_plan(plan)
                    break
                else:
                    logging.error(
                        "MP couldn't find path to the base location. Attempt {} of {}".format(attempt, max_attempts)
                    )

            if attempt == max_attempts:
                logging.error("MP failed after {} attempts. Exiting".format(max_attempts))
                sys.exit()

        base_pose2 = [-0.8095714332404795, -0.5171366166566791, 3.0351865450216153]
        for attempt in range(1, max_attempts + 1):
            plan = motion_planner.plan_base_motion(base_pose2)
            if plan is not None and len(plan) > 0:
                motion_planner.visualize_base_path(plan)
                break
            else:
                logging.error(
                    "MP couldn't find path to the base location. Attempt {} of {}".format(attempt, max_attempts)
                )
        if attempt == max_attempts:
            logging.error("MP failed after {} attempts. Exiting".format(max_attempts))
            sys.exit()

        env.robots[0].untuck()

        success = False
        for attempt in range(1, max_attempts + 1):
            pushing_position = [-1.36, -0.45, 0.67]
            pushing_direction = [-0.999, -0.015, -0.04]

            # For Fetch, and if the flag is activated, we push with the hand oriented top-down
            top_down_ee_pushing_orn = True
            ee_pushing_orn = (
                (0, np.pi / 2, -np.pi / 2) if top_down_ee_pushing_orn and env.robots[0].model_name == "Fetch" else None
            )

            # For the BehaviorRobot, we need to have longer pre-pushing distance or the prepush location will be in contact
            pre_pushing_distance = 0.1 if env.robots[0].model_name != "BehaviorRobot" else 0.2

            pre_push_path, pushing_interaction_path = motion_planner.plan_ee_push(
                pushing_position,
                np.array(pushing_direction),
                pre_pushing_distance=pre_pushing_distance,
                ee_pushing_orn=ee_pushing_orn,
            )
            if (
                pre_push_path is not None
                and len(pre_push_path) > 0
                and pushing_interaction_path is not None
                and len(pushing_interaction_path) > 0
            ):
                print("Visualizing planned arm path")
                full_path = np.concatenate((np.array(pre_push_path), np.array(pushing_interaction_path)))
                motion_planner.visualize_arm_path(full_path)
                print("End of the visualization")

                # TODO: execution!
                success = True
                break
            else:
                logging.error(
                    "MP couldn't find path to the arm pushing location. Attempt {} of {}".format(attempt, max_attempts)
                )
        if not success:
            logging.error("MP failed after {} attempts. Exiting".format(max_attempts))
            sys.exit()

    else:
        # Set viewer camera and directly set mode to planning mode
        env.simulator.viewer.initial_pos = [1.5, 0.1, 2.3]
        env.simulator.viewer.initial_view_direction = [-0.7, -0.3, -0.6]
        env.simulator.viewer.reset_viewer()
        env.simulator.viewer.mode = ViewerMode.PLANNING
        # Print out helpful information for this demo
        print_mp_info()

        while True:
            action = np.zeros(env.action_space.shape)
            state, reward, done, _ = env.step(action)

    env.close()


def main(selection="user", headless=False, short_exec=False):
    """
    Example of usage of the motion planner wrapper
    Creates an Rs_int scene, loads a Fetch and a MP wrapper
    The user can select to control the MP through the GUI or see the execution of a series of programmatic base
    and arm goals
    """
    print("*" * 80 + "\nDescription:" + main.__doc__ + "*" * 80)

    # Assuming that if selection!="user", headless=True, short_exec=True, we are calling it from tests and we
    # do not want to parse args (it would fail because the calling function is pytest "testfile.py")
    if not (selection != "user" and headless and short_exec):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--config",
            "-c",
            # behavior_robot_motion_planning.yaml, fetch_motion_planning.yaml, tiago_motion_planning.yaml
            default=os.path.join(igibson.configs_path, "tiago_motion_planning.yaml"),
            help="which config file to use [default: use yaml files in examples/configs]",
        )
        parser.add_argument(
            "--programmatic",
            "-p",
            dest="programmatic_actions",
            action="store_true",
            help="if the motion planner should be used with the GUI or programmatically",
        )
        args = parser.parse_args()
        config = args.config
        programmatic_actions = args.programmatic_actions
    else:
        # behavior_robot_motion_planning.yaml, fetch_motion_planning.yaml, tiago_motion_planning.yaml
        config = os.path.join(igibson.configs_path, "behavior_robot_motion_planning.yaml")
        programmatic_actions = True
    run_example(config, programmatic_actions, headless, short_exec)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
