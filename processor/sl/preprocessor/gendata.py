
import argparse
import os
import pickle
import sys

import numpy as np
from numpy.lib.format import open_memmap

from .gendata_feeder import Gendata_Feeder
from .preprocessor import Preprocessor


class Gendata_Preprocessor(Preprocessor):
    """
        Generate data
    """

    def __init__(self, argv=None):
        super().__init__(argv)
        self.joints = self.arg.gendata['joints']
        self.channels = self.arg.gendata['channels']
        self.num_person = self.arg.gendata['num_person']
        self.max_frames = self.arg.gendata['max_frames']

    def start(self):
        input_dir = '{}/holdout'.format(self.arg.work_dir)
        output_dir = '{}/datagen'.format(self.arg.work_dir)
        self.ensure_dir_exists(output_dir)

        print("Source directory: {}".format(input_dir))
        print("Generating data to '{}'...".format(output_dir))

        parts = ['train', 'test', 'val']
        joints = self.joints

        if self.arg.debug:
            joints = 18

        for part in parts:
            data_path = '{}/{}'.format(input_dir, part)
            label_path = '{}/{}_label.json'.format(input_dir, part)
            data_out_path = '{}/{}_data.npy'.format(output_dir, part)
            label_out_path = '{}/{}_label.pkl'.format(output_dir, part)
            debug = self.arg.debug

            if not os.path.isfile(label_path):
                print("Nothing to generate")
            else:
                print("Generating '{}' data...".format(part))
                self.gendata(data_path, label_path, data_out_path, label_out_path,
                             num_person_in=self.num_person,
                             num_person_out=self.num_person,
                             max_frame=self.max_frames,
                             joints=joints,
                             channels=self.channels,
                             debug=debug)

        print("Data generation finished.")

    def gendata(self,
                data_path,
                label_path,
                data_out_path,
                label_out_path,
                num_person_in,  # observe the first 5 persons
                num_person_out,  # then choose 2 persons with the highest score
                joints,
                max_frame,
                channels,
                debug=False):

        feeder = Gendata_Feeder(
            data_path=data_path,
            label_path=label_path,
            num_person_in=num_person_in,
            num_person_out=num_person_out,
            window_size=max_frame,
            joints=joints,
            channels=channels,
            debug=debug)

        sample_name = feeder.sample_name
        sample_label = []

        fp = open_memmap(
            data_out_path,
            dtype='float32',
            mode='w+',
            shape=(len(sample_name), channels, max_frame, joints, num_person_out))

        total = len(sample_name)

        for i, _ in enumerate(sample_name):
            data, label = feeder[i]
            self.progress_bar(i+1, total)
            fp[i, :, 0:data.shape[1], :, :] = data
            sample_label.append(label)

        with open(label_out_path, 'wb') as f:
            pickle.dump((sample_name, list(sample_label)), f)
