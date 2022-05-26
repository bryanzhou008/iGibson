import numpy as np

index_action_mapping = {
    0: 'move',
    1: 'pick',
    2: 'place',
    3: 'toggle',
    4: 'pull',
    5: 'push',
    6: 'vis_pick',
    7: 'vis_place'
}

skill_object_offset_params = {
    0:  # skill id: move
        {
            'printer.n.03_1': [-0.7, 0, 0, 0],  # dx, dy, dz, target_yaw
            'table.n.02_1': [0, -0.6, 0, 0.5 * np.pi],
            # Pomaria_1_int, 2
            'hamburger.n.01_1': [0, -0.8, 0, 0.5 * np.pi],
            'hamburger.n.01_2': [0, -0.7, 0, 0.5 * np.pi],
            'hamburger.n.01_3': [0, -0.8, 0, 0.5 * np.pi],
            'ashcan.n.01_1': [0, 0.8, 0, -0.5 * np.pi],
            'countertop.n.01_1': [[0.0, -0.8, 0, 0.1 * np.pi], [0.0, -0.8, 0, 0.5 * np.pi], [0.0, -0.8, 0, 0.8 * np.pi],],  # [0.1, 0.5, 0.8 1.0]
            # # Ihlen_1_int, 0
            # 'hamburger.n.01_1': [0, 0.8, 0, -0.5 * np.pi],
            # 'hamburger.n.01_2': [0, 0.8, 0, -0.5 * np.pi],
            # 'hamburger.n.01_3': [-0.2, 0.7, 0, -0.6 * np.pi],
            # 'ashcan.n.01_1': [-0.2, -0.5, 0, 0.4 * np.pi],
            # 'countertop.n.01_1': [-0.5, -0.6, 0, 0.5 * np.pi],
            # putting_away_Halloween_decorations
            'pumpkin.n.02_1': [0.4, 0.0, 0.0, 1.0 * np.pi],
            'pumpkin.n.02_2': [0, -0.5, 0, 0.5 * np.pi],
            'cabinet.n.01_1': [0.4, -1.15, 0, 0.5 * np.pi],
         },
    1: # pick
        {
            'printer.n.03_1': [-0.2, 0.0, 0.2],  # dx, dy, dz
            # Pomaria_1_int, 2
            'hamburger.n.01_1': [0.0, 0.0, 0.025],
            'hamburger.n.01_2': [0.0, 0.0, 0.025,],
            'hamburger.n.01_3': [0.0, 0.0, 0.025,],
            # putting_away_Halloween_decorations
            'pumpkin.n.02_1': [0.0, 0.0, 0.025,],
            'pumpkin.n.02_2': [0.0, 0.0, 0.025,],
        },
    2:  # place
        {
            'table.n.02_1': [0, 0, 0.5],  # dx, dy, dz
            # Pomaria_1_int, 2
            # 'ashcan.n.01_1': [0, 0, 0.5],
            # Ihlen_1_int, 0
            'ashcan.n.01_1': [0, 0, 0.5],
            # putting_away_Halloween_decorations
            'cabinet.n.01_1': [0.3, -0.55, 0.25],
        },
    3: # toggle
        {
            'printer.n.03_1': [-0.3, -0.25, 0.23],  # dx, dy, dz
        },
    4:  # pull
        {
            'cabinet.n.01_1': [0.3, -0.55, 0.35],  # dx, dy, dz
        },
    5:  # push
        {
            'cabinet.n.01_1': [0.3, -0.8, 0.35],  # dx, dy, dz
        },
    6:  # vis_pick
        {
            'hamburger.n.01_1': [0, -0.8, 0, 0.5 * np.pi, 0.0, 0.0, 0.025],
            'hamburger.n.01_2': [0, -0.7, 0, 0.5 * np.pi, 0.0, 0.0, 0.025,],
            'hamburger.n.01_3': [0, -0.8, 0, 0.5 * np.pi, 0.0, 0.0, 0.025,],
        },
    7:  # vis_place
        {
            'ashcan.n.01_1': [0, 0.8, 0, -0.5 * np.pi, 0, 0, 0.5],
        },
}

action_list_installing_a_printer = [
    [0, 'printer.n.03_1'],  # skill id, target_obj
    [1, 'printer.n.03_1'],
    [0, 'table.n.02_1'],
    [2, 'table.n.02_1'],
    [3, 'printer.n.03_1'],
]

# action_list_throwing_away_leftovers = [
#     [0, 'hamburger.n.01_1'],
#     [1, 'hamburger.n.01_1'],
#     [0, 'ashcan.n.01_1'],
#     [2, 'ashcan.n.01_1'],  # place
#     [0, 'hamburger.n.01_2'],
#     [1, 'hamburger.n.01_2'],
#     [0, 'ashcan.n.01_1'],
#     [2, 'ashcan.n.01_1'],  # place
#     [0, 'hamburger.n.01_3'],
#     [1, 'hamburger.n.01_3'],
#     [0, 'ashcan.n.01_1'],
#     [2, 'ashcan.n.01_1'],  # place
# ]*4

action_list_throwing_away_leftovers_v1 = [
    [0, 'hamburger.n.01_1'],
    [1, 'hamburger.n.01_1'],
    [0, 'ashcan.n.01_1'],
    [2, 'ashcan.n.01_1'],  # place
    [0, 'hamburger.n.01_2'],
    [1, 'hamburger.n.01_2'],
    [0, 'hamburger.n.01_3'],
    [1, 'hamburger.n.01_3'],
]

# action_list_throwing_away_leftovers = [
#     [0, 'countertop.n.01_1'],
#     [6, 'hamburger.n.01_1'],
#     [0, 'ashcan.n.01_1'],
#     [7, 'ashcan.n.01_1'],  # place
#     # [0, 'hamburger.n.01_2'],
#     [6, 'hamburger.n.01_2'],
#     # [0, 'hamburger.n.01_3'],
#     [6, 'hamburger.n.01_3'],
# ]

action_list_throwing_away_leftovers = [
    [0, 'countertop.n.01_1', 0],
    [6, 'hamburger.n.01_2'],  # 1: 137, 2: 138, 3: 139, plate: 135, ashcan: 140
    [0, 'ashcan.n.01_1'],
    [7, 'ashcan.n.01_1'],  # place
    [0, 'countertop.n.01_1', 1],
    [6, 'hamburger.n.01_1'],
    [0, 'ashcan.n.01_1'],
    [7, 'ashcan.n.01_1'],  # place
    [0, 'countertop.n.01_1', 2],
    [6, 'hamburger.n.01_3'],
    [0, 'ashcan.n.01_1'],
    [7, 'ashcan.n.01_1'],  # place
]

action_list_putting_leftovers_away = [
    [0, 'pasta.n.02_1'],
    [1, 'pasta.n.02_1'],
    [0, 'countertop.n.01_1'],
    [2, 'countertop.n.01_1'],  # place
    [0, 'pasta.n.02_2'],
    [1, 'pasta.n.02_2'],
    [0, 'countertop.n.01_1'],
    [2, 'countertop.n.01_1'],  # place
    [0, 'pasta.n.02_2_3'],
    [1, 'pasta.n.02_2_3'],
    [0, 'countertop.n.01_1'],
    [2, 'countertop.n.01_1'],  # place
    [0, 'pasta.n.02_2_4'],
    [1, 'pasta.n.02_2_4'],
    [0, 'countertop.n.01_1'],
    [2, 'countertop.n.01_1'],  # place
]

action_list_putting_away_Halloween_decorations = [
    [0, 'cabinet.n.01_1'],  # move
    [4, 'cabinet.n.01_1'],  # pull
    [0, 'pumpkin.n.02_1'],  # move
    [1, 'pumpkin.n.02_1'],  # pick
    [0, 'cabinet.n.01_1'],  # move
    [2, 'cabinet.n.01_1'],  # place
    [0, 'pumpkin.n.02_2'],  # move
    [1, 'pumpkin.n.02_2'],  # pick
    [0, 'cabinet.n.01_1'],  # move
    [2, 'cabinet.n.01_1'],  # place
    [5, 'cabinet.n.01_1'],  # push
]


action_dict = {'installing_a_printer': action_list_installing_a_printer,
               'throwing_away_leftovers': action_list_throwing_away_leftovers,
               'putting_leftovers_away': action_list_putting_leftovers_away,
               'putting_away_Halloween_decorations': action_list_putting_away_Halloween_decorations}