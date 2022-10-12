import collections
import itertools
import logging
import os
import random
from sys import platform

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import igibson
from igibson import object_states
from igibson.envs.igibson_env import iGibsonEnv
from igibson.objects.visual_marker import VisualMarker
from igibson.render.mesh_renderer.mesh_renderer_settings import MeshRendererSettings
from igibson.utils.constants import MAX_INSTANCE_COUNT
from igibson.utils.derivative_dataset import filters, generators, perturbers

RENDER_WIDTH = 1024
RENDER_HEIGHT = 1024

REQUESTED_IMAGES = 10000
IMAGES_PER_PERTURBATION = 10
MAX_ATTEMPTS_PER_PERTURBATION = 1000

MAX_DEPTH = 5  # meters

DEBUG_FILTERS = True
DEBUG_FILTER_IMAGES = True

OUTPUT_DIR = r"C:\Users\cgokmen\research\derivative_dataset_tests"

GENERATORS = [
    # generators.uniform_generator,
    generators.object_targeted_generator,
]

PERTURBERS = [
    perturbers.object_boolean_state_randomizer(object_states.Open),
]

FILTERS = {
    "no_collision": filters.point_in_object_filter(),
    "no_openable_objects_fov": filters.no_relevant_object_in_fov_filter(object_states.Open, min_bbox_vertices_in_fov=4),
    "no_openable_objects_img": filters.no_relevant_object_in_img_filter(object_states.Open, threshold=0.05),
    "some_objects_closer_than_10cm": filters.too_close_filter(min_dist=0.1),
    # At least 70% of the image between 30cm and 2m away
    # "too_many_too_close_far_objects": filters.too_close_filter(min_dist=0.5, max_dist=3., max_allowed_fraction_outside_threshold=0.3),
    # No more than 50% of the image should consist of wall/floor/ceiling
    "too_much_structure": filters.too_much_structure(max_allowed_fraction_of_structure=0.5),
    # More than 33% of the image should not be the same object.
    "too_much_of_the_same_object": filters.too_much_of_same_object_in_fov_filter(threshold=0.5),
}

FILTER_IMG_IDX = {f: 0 for f in FILTERS}


def run_filters(env, objs_of_interest):
    for filter_name, filter_fn in FILTERS.items():
        if not filter_fn(env, objs_of_interest):
            print("Failed ", filter_name)
            FILTER_IMG_IDX[filter_name] += 1

            if DEBUG_FILTERS and random.uniform(0, 1) < 0.01:
                x = np.arange(len(FILTER_IMG_IDX))
                h = list(FILTER_IMG_IDX.values())
                l = list(FILTER_IMG_IDX.keys())
                plt.bar(x, h)
                plt.xticks(x, l)
                plt.show()

                if DEBUG_FILTER_IMAGES:
                    filter_img_path = os.path.join(OUTPUT_DIR, "filters", filter_name)
                    os.makedirs(filter_img_path, exist_ok=True)
                    (rgb,) = env.simulator.renderer.render(("rgb"))
                    rgb_img = Image.fromarray(np.uint8(rgb[:, :, :3] * 255))
                    rgb_img.save(os.path.join(filter_img_path, f"{FILTER_IMG_IDX[filter_name]}.png"))

            return False

    return True


def save_images(env, objs_of_interest, img_id):
    rgb, segmask, threed = env.simulator.renderer.render(("rgb", "seg", "3d"))

    rgb_arr = np.uint8(rgb[:, :, :3] * 255)
    rgb_img = Image.fromarray(rgb_arr)
    depth = np.clip(threed[:, :2:3], 0, MAX_DEPTH) / MAX_DEPTH
    depth_arr = np.uint8(depth[..., 0] * 255)
    depth_img = Image.fromarray(depth_arr)

    seg = np.round(segmask[:, :, 0] * MAX_INSTANCE_COUNT).astype(int)
    body_ids = env.simulator.renderer.get_pb_ids_for_instance_ids(seg)
    seg_arr = np.uint8(body_ids)
    seg_img = Image.fromarray(seg_arr)

    out_dir = os.path.join(OUTPUT_DIR, "uncropped")
    rgb_img.save(os.path.join(out_dir, "rgb", f"{img_id}.png"))
    depth_img.save(os.path.join(out_dir, "depth", f"{img_id}.png"))
    seg_img.save(os.path.join(out_dir, "seg", f"{img_id}.png"))

    obj_body_ids = [x for obj in objs_of_interest for x in obj.get_body_ids()]
    found_obj_body_ids = set(body_ids.flatten()) & set(obj_body_ids)
    found_objs = {env.simulator.scene.objects_by_id[x] for x in found_obj_body_ids}

    crop_out_dir = os.path.join(OUTPUT_DIR, "cropped")
    for crop_id, obj in enumerate(found_objs):
        this_obj_body_ids = obj.get_body_ids()
        this_obj_pixels = np.isin(body_ids, this_obj_body_ids)
        rows = np.any(this_obj_pixels, axis=1)
        cols = np.any(this_obj_pixels, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        # crop the images
        cropped_rgb = Image.fromarray(rgb_arr[rmin : rmax + 1, cmin : cmax + 1])
        cropped_depth = Image.fromarray(depth_arr[rmin : rmax + 1, cmin : cmax + 1])
        cropped_seg = Image.fromarray(seg_arr[rmin : rmax + 1, cmin : cmax + 1])

        label = "open" if obj.states[object_states.Open].get_value() else "closed"

        labeled_out_dir = os.path.join(crop_out_dir, label)
        cropped_rgb.save(os.path.join(labeled_out_dir, "rgb", f"{img_id}_{crop_id}.png"))
        cropped_depth.save(os.path.join(labeled_out_dir, "depth", f"{img_id}_{crop_id}.png"))
        cropped_seg.save(os.path.join(labeled_out_dir, "seg", f"{img_id}_{crop_id}.png"))


def main(headless=False, short_exec=False):
    """
    Prompts the user to select any available interactive scene and loads it.
    Shows how to load directly scenes without the Environment interface
    Shows how to sample points in the scene by room type and how to compute geodesic distance and the shortest path
    """
    scene_id = "Rs_int"
    hdr_texture = os.path.join(igibson.ig_dataset_path, "scenes", "background", "probe_02.hdr")
    hdr_texture2 = os.path.join(igibson.ig_dataset_path, "scenes", "background", "probe_03.hdr")
    light_modulation_map_filename = os.path.join(
        igibson.ig_dataset_path, "scenes", "Rs_int", "layout", "floor_lighttype_0.png"
    )
    background_texture = os.path.join(igibson.ig_dataset_path, "scenes", "background", "urban_street_01.jpg")

    rendering_settings = MeshRendererSettings(
        optimized=True,
        fullscreen=False,
        env_texture_filename=hdr_texture,
        env_texture_filename2=hdr_texture2,
        env_texture_filename3=background_texture,
        light_modulation_map_filename=light_modulation_map_filename,
        enable_shadow=True,
        enable_pbr=True,
        msaa=False,
        light_dimming_factor=1.0,
    )
    env = iGibsonEnv(
        scene_id=scene_id,
        mode="gui_interactive",
        config_file={
            "image_width": RENDER_WIDTH,
            "image_height": RENDER_HEIGHT,
            "vertical_fov": 60,
            "scene": "igibson",
        },
        rendering_settings=rendering_settings,
    )

    for _ in range(100):
        env.step(None)

    total_image_count = 0
    perturbers = itertools.cycle(PERTURBERS)
    while total_image_count < REQUESTED_IMAGES:
        perturber = next(perturbers)
        env.simulator.scene.reset_scene_objects()
        for _ in range(100):
            env.step(None)

        objs_of_interest = perturber(env)
        env.simulator.sync(force_sync=True)

        perturbation_image_count = 0
        attempts = 0
        generators = itertools.cycle(GENERATORS)
        while perturbation_image_count < IMAGES_PER_PERTURBATION and attempts < MAX_ATTEMPTS_PER_PERTURBATION:
            print("Attempt ", attempts)
            attempts += 1
            generator = next(generators)

            camera_pos, camera_target, camera_up = generator(env, objs_of_interest)
            env.simulator.renderer.set_camera(camera_pos, camera_target, camera_up)

            # v = VisualMarker(radius=0.1)
            # env.simulator.import_object(v)
            # v.set_position(camera_pos)

            if not run_filters(env, objs_of_interest):
                continue

            save_images(env, objs_of_interest, total_image_count)

            perturbation_image_count += 1
            total_image_count += 1

    env.simulator.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
