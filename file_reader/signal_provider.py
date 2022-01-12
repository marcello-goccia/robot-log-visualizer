import time
from datetime import datetime

import h5py
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread
from threading import Lock


class SignalProvider(QThread):
    update_index = pyqtSignal()

    def __init__(self, meshcat_visualizer, initial_time, visualization_fps):
        QThread.__init__(self)

        # set device state
        self._state = 'pause'
        self.state_lock = Lock()

        self._last_data = None

        # Index expressed in seconds
        self._index = 0
        self.index_lock = Lock()

        self.current_time = initial_time
        self.visualization_fps = visualization_fps
        self.meshcat_visualizer = meshcat_visualizer

        self.s = np.array([])

        self.timestamps = np.array([])
        self.final_timestamp = 0

    def open_mat_file(self, file_name: str):
        with h5py.File(file_name, 'r') as f:

            self.s = np.squeeze(np.array(f['robot_logger_device']['joints_state']['positions']['data']))

            timestamps = np.array(f['robot_logger_device']['joints_state']['positions']['timestamps'])
            initial_timestamp = np.array(f['robot_logger_device']['joints_state']['positions']['timestamps'])[0]
            self.timestamps = timestamps - initial_timestamp
            final_timestamp = np.array(f['robot_logger_device']['joints_state']['positions']['timestamps'])[-1] - initial_timestamp
            self.final_timestamp = final_timestamp[0]

            self.index = 0

    # Length in seconds
    def __len__(self):
        return int(self.final_timestamp)

    @property
    def state(self):
        self.state_lock.acquire()
        value = self._state
        self.state_lock.release()
        return value

    @state.setter
    def state(self, new_state):
        self.state_lock.acquire()
        self._state = new_state
        self.state_lock.release()

    @property
    def index(self):
        self.index_lock.acquire()
        value = self._index
        self.index_lock.release()
        return value

    @index.setter
    def index(self, index):
        self.index_lock.acquire()
        self._index = index
        self.index_lock.release()

    def register_update_index(self, slot):
        self.update_index.connect(slot)

    def run(self):
        while True:
            if self.state == 'running':

                # Find the datapoint which is closest to the current index
                self._last_data = self.find_last_data(self.index)

                R = np.eye(3)
                p = np.array([0.0, 0.0, 0.0])
                self.meshcat_visualizer.display(p, R, self._last_data)

                self.index = self.index + 1/self.visualization_fps
                self.update_index.emit()

            self.synchronize()

    def synchronize(self):
        if self.current_time + 1/self.visualization_fps - datetime.now().timestamp() > 0:
            time.sleep(self.current_time + 1/self.visualization_fps - datetime.now().timestamp())
        else:
            # Debug to check whether the synchronization takes place or not
            print("no synch MESHCAT!")
        self.current_time = self.current_time + 1/self.visualization_fps

    def find_last_data(self, index):

        data_index = np.searchsorted(self.timestamps[:,0],index)
        return self.s[data_index, :]







