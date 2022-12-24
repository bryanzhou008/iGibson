import logging
import os
import time
import pybullet as p
import pybullet_data
import argparse
import numpy as np
import datetime
import random
import json

import igibson
from igibson.objects.articulated_object import ArticulatedObject
from igibson.objects.visual_marker import VisualMarker
from igibson.render.mesh_renderer.mesh_renderer_cpu import MeshRendererSettings
from igibson.render.mesh_renderer.mesh_renderer_vr import VrSettings
from igibson.robots import BehaviorRobot
from igibson.scenes.empty_scene import EmptyScene
from igibson.scenes.igibson_indoor_scene import InteractiveIndoorScene
from igibson.utils.ig_logging import IGLogWriter

from simple_task import catch, navigate, place, slice, throw, wipe


# HDR files for PBR rendering
from igibson.simulator_vr import SimulatorVR
from igibson.utils.utils import parse_config

hdr_texture = os.path.join(igibson.ig_dataset_path, "scenes", "background", "probe_02.hdr")
hdr_texture2 = os.path.join(igibson.ig_dataset_path, "scenes", "background", "probe_03.hdr")
light_modulation_map_filename = os.path.join(
    igibson.ig_dataset_path, "scenes", "Wainscott_1_int", "layout", "floor_lighttype_0.png"
)
background_texture = os.path.join(igibson.ig_dataset_path, "scenes", "background", "urban_street_01.jpg")


vi_choices = ["normal", "cataract", "amd", "glaucoma", "presbyopia", "myopia"]
max_num_trials = 5

def load_scene(simulator, task):
    """Setup scene"""
    if task == "slice":
        scene = InteractiveIndoorScene(
            "Rs_int", load_object_categories=["walls", "floors", "ceilings"], load_room_types=["kitchen"]
        )
        simulator.import_scene(scene)
    else:
        # scene setup
        scene = EmptyScene(floor_plane_rgba=[0.5, 0.5, 0.5, 0.5])
        simulator.import_scene(scene)
        if task == "catch":
            # wall setup
            wall = ArticulatedObject(
                "igibson/examples/vr/visual_disease_demo_mtls/plane/white_plane.urdf", scale=1, rendering_params={"use_pbr": False, "use_pbr_mapping": False}
            )
            simulator.import_object(wall)
            wall.set_position_orientation([19, 0, 0], [0, 0.707, 0, 0.707])
        else:
            walls_pos = [
                ([-15, 0, 0], [0.5, 0.5, 0.5, 0.5]),
                ([15, 0, 0], [0.5, 0.5, 0.5, 0.5]),
                ([0, -15, 0], [0.707, 0, 0, 0.707]),
                ([0, 15, 0], [0.707, 0, 0, 0.707])
            ]
            for i in range(4):
                wall = ArticulatedObject(
                    "igibson/examples/vr/visual_disease_demo_mtls/plane/white_plane.urdf", scale=1, rendering_params={"use_pbr": False, "use_pbr_mapping": False}
                )
                simulator.import_object(wall)
                wall.set_position_orientation(walls_pos[i][0], walls_pos[i][1])


def parse_args():
    tasks_choices = ["catch", "navigate", "place", "slice", "throw", "wipe"]
    parser = argparse.ArgumentParser(description="Run and collect a demo of a task")
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        nargs="?",
        help="Name of the experiment subject",
    )
    parser.add_argument(
        "--task",
        type=str,
        choices=tasks_choices,
        required=False,
        default="catch",
        nargs="?",
        help="Name of task to collect a demo of. Choose from catch/navigate/place/slice/slice/throw/wipe",
    )
    parser.add_argument(
        "--vi",
        type=str,
        choices=vi_choices,
        required=False,
        default="normal",
        nargs="?",
        help="Mode of visual impairment. Choose from normal/cataract/amd/glaucoma/myopia/presbyopia",
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=[1, 2, 3],
        required=False,
        default=1,
        nargs="?",
        help="Level of visual impairment. Choose from 1/2/3",
    )
    parser.add_argument("--disable_save", action="store_true", help="Whether to disable saving logfiles.")
    parser.add_argument("--debug", action="store_true", help="Whether to enable debug mode (right controller to switch between modes and levels).")
    return parser.parse_args()

def main():
    args = parse_args()
    if not args.disable_save:
        save_dir = f"igibson/data/demos/{args.name}/{args.task}/{args.vi}_{args.level}/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(save_dir, exist_ok=False)
    # get seed for this expriment's configuration
    with open("igibson/examples/vr/visual_disease_demo_mtls/seed.json", "r") as f:
        seed_num = json.load(f)[args.task][args.vi][args.level - 1]
        random.seed(seed_num)
        np.random.seed(seed_num)
    
    lib = {
        "catch": catch,
        "navigate": navigate,
        "place": place,
        "slice": slice,
        "throw": throw,
        "wipe": wipe,
    }[args.task]
    
    if args.task == "navigate":
        vr_rendering_settings = MeshRendererSettings(
            optimized=True,
            fullscreen=False,
            env_texture_filename="",
            env_texture_filename2="",
            env_texture_filename3="",
            light_modulation_map_filename="",
            enable_pbr=False,
            msaa=True,
            light_dimming_factor=1.0,
        )
        gravity = 0
    else:
        vr_rendering_settings = MeshRendererSettings(
            optimized=True,
            fullscreen=False,
            env_texture_filename=hdr_texture,
            env_texture_filename2=hdr_texture2,
            env_texture_filename3="",
            light_modulation_map_filename=light_modulation_map_filename,
            enable_shadow=True,
            enable_pbr=True,
            msaa=True,
            light_dimming_factor=1.0,
        )
        gravity = 9.8

    # task specific vr settings 
    vr_settings = VrSettings(use_vr=True)
    vr_settings.touchpad_movement = False

    s = SimulatorVR(gravity = gravity, render_timestep=1/90.0, physics_timestep=1/360.0, mode="vr", rendering_settings=vr_rendering_settings, vr_settings=vr_settings)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    # scene setup
    load_scene(s, args.task)
    # robot setup
    config = parse_config(os.path.join(igibson.configs_path, "visual_disease.yaml"))
    bvr_robot = BehaviorRobot(**config["robot"])
    s.import_object(bvr_robot)
    # object setup
    objs = lib.import_obj(s)
    # import a visual marker for robot's initial pose
    robot_pos_marker = VisualMarker(visual_shape=p.GEOM_CYLINDER, rgba_color=[1, 0, 0, 0.1], radius=0.1, length=1)
    s.import_object(robot_pos_marker)
    robot_pos_marker.set_position([0, 0, 0.5])
    for instance in robot_pos_marker.renderer_instances:
        instance.hidden = True
    
    trial_id = 0

    task_success_list = []
    task_completion_time = []

    # set robot to default pose to avoid controller vibration
    bvr_robot.set_position_orientation(*lib.default_robot_pose)
    s.set_vr_offset([*lib.default_robot_pose[0][:2], 0])
    
    # Display welcome message
    overlay_text = s.add_vr_overlay_text(
        text_data=lib.intro_paragraph,
        font_size=40,
        font_style="Bold",
        color=[0, 0, 0],
        pos=[0, 75],
        size=[100, 80],
    )
    s.set_hud_show_state(True)
    s.renderer.update_vi_mode(mode=6) # black screen
    s.step()
    while not s.query_vr_event("right_controller", "overlay_toggle"):
        s.step()
    s.set_hud_show_state(False)
    s.renderer.update_vi_mode(vi_choices.index(args.vi))
    s.renderer.update_vi_level(level=args.level)
    
    while True:
        start_time = time.time()
        # Reset robot to default position
        bvr_robot.set_position_orientation(*lib.default_robot_pose)
        s.set_vr_offset([*lib.default_robot_pose[0][:2], 0])
        # set all object positions
        ret = lib.set_obj_pos(objs)
        # log writer
        log_writer = None
        if not args.disable_save:
            demo_file = f"{save_dir}/{trial_id}.hdf5"
            log_writer = IGLogWriter(
                s,
                log_filepath=demo_file,
                task=None,
                store_vr=True,
                vr_robot=bvr_robot,
                filter_objects=True,
            )
            log_writer.set_up_data_storage()
            log_writer.hf.attrs["/metadata/instance_id"] = trial_id
        
        # Main simulation loop
        s.vr_attached = True
        success, terminate = lib.main(s, log_writer, args.disable_save, args.debug, bvr_robot, objs, ret)
        
        if not args.disable_save:
            log_writer.end_log_session()
        
        task_success_list.append(success)
        task_completion_time.append(time.time() - start_time)
        trial_id += 1

        if terminate or trial_id == max_num_trials:
            break
        
        # start transition period
        # Display transition (task completion) message
        overlay_text.set_text(f"""Task {args.task} with {args.vi} level{args.level} trial #{trial_id} complete! \nToggle menu button on the left controller to finish data collection...\n To restart the task, return to the original position, then toggle menu button on the right controller.""")
        s.set_hud_show_state(True)
        # Temporarily disable visual impairment
        s.renderer.update_vi_mode(0)
        for instance in robot_pos_marker.renderer_instances:
            instance.hidden = False
        while True:
            s.step()
            bvr_robot.apply_action(s.gen_vr_robot_action())
            if s.query_vr_event("left_controller", "overlay_toggle"):
                terminate = True
                break
            if s.query_vr_event("right_controller", "overlay_toggle"):
                # check robot position (need to return to original position)
                if np.linalg.norm(np.linalg.norm(bvr_robot.get_position()[:2] - [0, 0])) < 0.3:
                    break
        if terminate:
            break

        # restore task rendering settings for the next round
        for instance in robot_pos_marker.renderer_instances:
            instance.hidden = True
        s.set_hud_show_state(False)   
        s.renderer.update_vi_mode(vi_choices.index(args.vi))

    s.disconnect()
    if not args.disable_save:
        np.save(f"{save_dir}/success_list.npy", task_success_list)
        np.save(f"{save_dir}/completion_time.npy", task_completion_time)
    print(f"{args.task}_{args.vi}_{args.level} data collection complete! Total trial: {trial_id}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main() 