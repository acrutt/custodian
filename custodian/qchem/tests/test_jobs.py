# coding: utf-8

from __future__ import unicode_literals, division

import os
import shutil
from unittest import TestCase
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
import unittest

from custodian.qchem.jobs import QCJob
from pymatgen.io.qchem.inputs import QCInput

__author__ = "Samuel Blau"
__copyright__ = "Copyright 2018, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Samuel Blau"
__email__ = "samblau1@gmail.com"
__status__ = "Alpha"
__date__ = "6/6/18"
__credits__ = "Shyam Dwaraknath"

test_dir = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test_files", "qchem",
    "new_test_files")

scr_dir = os.path.join(test_dir, "scr")
cwd = os.getcwd()


class QCJobTest(TestCase):

    def test_defaults(self):
        with patch("custodian.qchem.jobs.shutil.copy") as copy_patch:
            myjob = QCJob(qchem_command="qchem", max_cores=32)
            self.assertEqual(myjob.current_command, ' qchem -nt 32 mol.qin mol.qout')
            myjob.setup()
            self.assertEqual(copy_patch.call_args_list[0][0][0], "mol.qin")
            self.assertEqual(copy_patch.call_args_list[0][0][1], "mol.qin.orig")
            self.assertEqual(os.environ["QCSCRATCH"],os.getcwd())
            self.assertEqual(os.environ["QCTHREADS"],"32")
            self.assertEqual(os.environ["OMP_NUM_THREADS"],"32")

    def test_not_defaults(self):
        myjob = QCJob(qchem_command="qchem -slurm", multimode="mpi", input_file="different.qin", output_file="not_default.qout", max_cores=12, scratch_dir="/not/default/scratch/", backup=False)
        self.assertEqual(myjob.current_command, ' qchem -slurm -np 12 different.qin not_default.qout')
        myjob.setup()
        self.assertEqual(os.environ["QCSCRATCH"],"/not/default/scratch/")

    def test_save_scratch(self):
        with patch("custodian.qchem.jobs.shutil.copy") as copy_patch:
            myjob = QCJob(qchem_command="qchem -slurm", max_cores=32, scratch_dir=os.getcwd(), save_scratch=True, save_name="freq_scratch")
            self.assertEqual(myjob.current_command, ' qchem -slurm -nt 32 mol.qin mol.qout freq_scratch')
            myjob.setup()
            self.assertEqual(copy_patch.call_args_list[0][0][0], "mol.qin")
            self.assertEqual(copy_patch.call_args_list[0][0][1], "mol.qin.orig")
            self.assertEqual(os.environ["QCSCRATCH"],os.getcwd())
            self.assertEqual(os.environ["QCTHREADS"],"32")
            self.assertEqual(os.environ["OMP_NUM_THREADS"],"32")

class OptFFTest(TestCase):
    def setUp(self):
        os.makedirs(scr_dir)
        shutil.copyfile(os.path.join(test_dir,"FF_working/test.qin"),os.path.join(scr_dir,"test.qin"))
        shutil.copyfile(os.path.join(test_dir,"FF_working/test.qout.opt_0"),os.path.join(scr_dir,"test.qout.opt_0"))
        shutil.copyfile(os.path.join(test_dir,"FF_working/test.qout.freq_0"),os.path.join(scr_dir,"test.qout.freq_0"))
        shutil.copyfile(os.path.join(test_dir,"FF_working/test.qout.opt_1"),os.path.join(scr_dir,"test.qout.opt_1"))
        shutil.copyfile(os.path.join(test_dir,"FF_working/test.qout.freq_1"),os.path.join(scr_dir,"test.qout.freq_1"))
        os.chdir(scr_dir)

    def tearDown(self):
        os.chdir(cwd)
        shutil.rmtree(scr_dir)

    def test_OptFF(self):
        myjob = QCJob.opt_with_frequency_flattener(qchem_command="qchem", max_cores=32, input_file="test.qin", output_file="test.qout", linked=False)
        expected_next = QCJob(
                        qchem_command="qchem",
                        max_cores=32,
                        multimode="openmp",
                        input_file="test.qin",
                        output_file="test.qout",
                        suffix=".opt_0",
                        backup=True).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        expected_next = QCJob(
                        qchem_command="qchem",
                        max_cores=32,
                        multimode="openmp",
                        input_file="test.qin",
                        output_file="test.qout",
                        suffix=".freq_0",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"FF_working/test.qin.freq_0")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"test.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem",
                        max_cores=32,
                        multimode="openmp",
                        input_file="test.qin",
                        output_file="test.qout",
                        suffix=".opt_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"FF_working/test.qin.opt_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"test.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem",
                        max_cores=32,
                        multimode="openmp",
                        input_file="test.qin",
                        output_file="test.qout",
                        suffix=".freq_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"FF_working/test.qin.freq_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"test.qin")).as_dict())
        self.assertRaises(StopIteration,myjob.__next__)

class OptFFTest1(TestCase):
    def setUp(self):
        os.makedirs(scr_dir)
        shutil.copyfile(os.path.join(test_dir,"2620_complete/mol.qin.orig"),os.path.join(scr_dir,"mol.qin"))
        shutil.copyfile(os.path.join(test_dir,"2620_complete/mol.qout.opt_0"),os.path.join(scr_dir,"mol.qout.opt_0"))
        os.chdir(scr_dir)

    def tearDown(self):
        os.chdir(cwd)
        shutil.rmtree(scr_dir)

    def test_OptFF(self):
        myjob = QCJob.opt_with_frequency_flattener(qchem_command="qchem -slurm", max_cores=32, input_file="mol.qin", output_file="mol.qout", linked=False)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_0",
                        backup=True).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertRaises(StopIteration,myjob.__next__)

class OptFFTest2(TestCase):
    def setUp(self):
        os.makedirs(scr_dir)
        shutil.copyfile(os.path.join(test_dir,"disconnected_but_converged/mol.qin.orig"),os.path.join(scr_dir,"mol.qin"))
        shutil.copyfile(os.path.join(test_dir,"disconnected_but_converged/mol.qout.opt_0"),os.path.join(scr_dir,"mol.qout.opt_0"))
        shutil.copyfile(os.path.join(test_dir,"disconnected_but_converged/mol.qout.freq_0"),os.path.join(scr_dir,"mol.qout.freq_0"))
        os.chdir(scr_dir)

    def tearDown(self):
        os.chdir(cwd)
        shutil.rmtree(scr_dir)

    def test_OptFF(self):
        myjob = QCJob.opt_with_frequency_flattener(qchem_command="qchem -slurm", max_cores=32, input_file="mol.qin", output_file="mol.qout", linked=False)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_0",
                        backup=True).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_0",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"disconnected_but_converged/mol.qin.freq_0")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        self.assertRaises(StopIteration,myjob.__next__)

class OptFFTestSwitching(TestCase):
    def setUp(self):
        os.makedirs(scr_dir)
        shutil.copyfile(os.path.join(test_dir,"FF_switching/mol.qin.orig"),os.path.join(scr_dir,"mol.qin"))
        shutil.copyfile(os.path.join(test_dir,"FF_switching/mol.qout.opt_0"),os.path.join(scr_dir,"mol.qout.opt_0"))
        shutil.copyfile(os.path.join(test_dir,"FF_switching/mol.qout.freq_0"),os.path.join(scr_dir,"mol.qout.freq_0"))
        shutil.copyfile(os.path.join(test_dir,"FF_switching/mol.qout.opt_1"),os.path.join(scr_dir,"mol.qout.opt_1"))
        shutil.copyfile(os.path.join(test_dir,"FF_switching/mol.qout.freq_1"),os.path.join(scr_dir,"mol.qout.freq_1"))
        shutil.copyfile(os.path.join(test_dir,"FF_switching/mol.qout.opt_2"),os.path.join(scr_dir,"mol.qout.opt_2"))
        shutil.copyfile(os.path.join(test_dir,"FF_switching/mol.qout.freq_2"),os.path.join(scr_dir,"mol.qout.freq_2"))
        os.chdir(scr_dir)

    def tearDown(self):
        os.chdir(cwd)
        shutil.rmtree(scr_dir)

    def test_OptFF(self):
        myjob = QCJob.opt_with_frequency_flattener(qchem_command="qchem -slurm", max_cores=32,input_file="mol.qin", output_file="mol.qout", linked=False)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_0",
                        backup=True).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_0",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"FF_switching/mol.qin.freq_0")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"FF_switching/mol.qin.opt_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"FF_switching/mol.qin.freq_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_2",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"FF_switching/mol.qin.opt_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_2",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"FF_switching/mol.qin.freq_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        self.assertRaises(StopIteration,myjob.__next__)

class OptFFTest6004(TestCase):
    def setUp(self):
        os.makedirs(scr_dir)
        shutil.copyfile(os.path.join(test_dir,"6004_frag12/mol.qin.orig"),os.path.join(scr_dir,"mol.qin"))
        shutil.copyfile(os.path.join(test_dir,"6004_frag12/mol.qout.opt_0"),os.path.join(scr_dir,"mol.qout.opt_0"))
        shutil.copyfile(os.path.join(test_dir,"6004_frag12/mol.qout.freq_0"),os.path.join(scr_dir,"mol.qout.freq_0"))
        shutil.copyfile(os.path.join(test_dir,"6004_frag12/mol.qout.opt_1"),os.path.join(scr_dir,"mol.qout.opt_1"))
        shutil.copyfile(os.path.join(test_dir,"6004_frag12/mol.qout.freq_1"),os.path.join(scr_dir,"mol.qout.freq_1"))
        shutil.copyfile(os.path.join(test_dir,"6004_frag12/mol.qout.opt_2"),os.path.join(scr_dir,"mol.qout.opt_2"))
        shutil.copyfile(os.path.join(test_dir,"6004_frag12/mol.qout.freq_2"),os.path.join(scr_dir,"mol.qout.freq_2"))
        os.chdir(scr_dir)

    def tearDown(self):
        os.chdir(cwd)
        shutil.rmtree(scr_dir)

    def test_OptFF(self):
        myjob = QCJob.opt_with_frequency_flattener(qchem_command="qchem -slurm", max_cores=32,input_file="mol.qin", output_file="mol.qout", linked=False)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_0",
                        backup=True).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_0",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"6004_frag12/mol.qin.freq_0")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"6004_frag12/mol.qin.opt_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"6004_frag12/mol.qin.freq_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_2",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"6004_frag12/mol.qin.opt_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_2",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"6004_frag12/mol.qin.freq_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())

class OptFFTest5952(TestCase):
    def setUp(self):
        os.makedirs(scr_dir)
        shutil.copyfile(os.path.join(test_dir,"5952_frag16/mol.qin.orig"),os.path.join(scr_dir,"mol.qin"))
        shutil.copyfile(os.path.join(test_dir,"5952_frag16/mol.qout.opt_0"),os.path.join(scr_dir,"mol.qout.opt_0"))
        shutil.copyfile(os.path.join(test_dir,"5952_frag16/mol.qout.freq_0"),os.path.join(scr_dir,"mol.qout.freq_0"))
        shutil.copyfile(os.path.join(test_dir,"5952_frag16/mol.qout.opt_1"),os.path.join(scr_dir,"mol.qout.opt_1"))
        shutil.copyfile(os.path.join(test_dir,"5952_frag16/mol.qout.freq_1"),os.path.join(scr_dir,"mol.qout.freq_1"))
        shutil.copyfile(os.path.join(test_dir,"5952_frag16/mol.qout.opt_2"),os.path.join(scr_dir,"mol.qout.opt_2"))
        shutil.copyfile(os.path.join(test_dir,"5952_frag16/mol.qout.freq_2"),os.path.join(scr_dir,"mol.qout.freq_2"))
        os.chdir(scr_dir)

    def tearDown(self):
        os.chdir(cwd)
        shutil.rmtree(scr_dir)

    def test_OptFF(self):
        myjob = QCJob.opt_with_frequency_flattener(qchem_command="qchem -slurm", max_cores=32,input_file="mol.qin", output_file="mol.qout", linked=False)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_0",
                        backup=True).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_0",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5952_frag16/mol.qin.freq_0")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5952_frag16/mol.qin.opt_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5952_frag16/mol.qin.freq_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_2",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5952_frag16/mol.qin.opt_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_2",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5952_frag16/mol.qin.freq_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        self.assertRaises(Exception,myjob.__next__)

class OptFFTest5690(TestCase):
    def setUp(self):
        os.makedirs(scr_dir)
        shutil.copyfile(os.path.join(test_dir,"5690_frag18/mol.qin.orig"),os.path.join(scr_dir,"mol.qin"))
        shutil.copyfile(os.path.join(test_dir,"5690_frag18/mol.qout.opt_0"),os.path.join(scr_dir,"mol.qout.opt_0"))
        shutil.copyfile(os.path.join(test_dir,"5690_frag18/mol.qout.freq_0"),os.path.join(scr_dir,"mol.qout.freq_0"))
        shutil.copyfile(os.path.join(test_dir,"5690_frag18/mol.qout.opt_1"),os.path.join(scr_dir,"mol.qout.opt_1"))
        shutil.copyfile(os.path.join(test_dir,"5690_frag18/mol.qout.freq_1"),os.path.join(scr_dir,"mol.qout.freq_1"))
        shutil.copyfile(os.path.join(test_dir,"5690_frag18/mol.qout.opt_2"),os.path.join(scr_dir,"mol.qout.opt_2"))
        shutil.copyfile(os.path.join(test_dir,"5690_frag18/mol.qout.freq_2"),os.path.join(scr_dir,"mol.qout.freq_2"))
        os.chdir(scr_dir)

    def tearDown(self):
        os.chdir(cwd)
        shutil.rmtree(scr_dir)

    def test_OptFF(self):
        myjob = QCJob.opt_with_frequency_flattener(qchem_command="qchem -slurm", max_cores=32,input_file="mol.qin", output_file="mol.qout", linked=False)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_0",
                        backup=True).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_0",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5690_frag18/mol.qin.freq_0")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5690_frag18/mol.qin.opt_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_1",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5690_frag18/mol.qin.freq_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_2",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5690_frag18/mol.qin.opt_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_2",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"5690_frag18/mol.qin.freq_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        self.assertRaises(Exception,myjob.__next__)

class OptFF_small_neg_freq(TestCase):
    def setUp(self):
        os.makedirs(scr_dir)
        shutil.copyfile(os.path.join(test_dir,"small_neg_freq/mol.qin.orig"),os.path.join(scr_dir,"mol.qin"))
        shutil.copyfile(os.path.join(test_dir,"small_neg_freq/mol.qout.opt_0"),os.path.join(scr_dir,"mol.qout.opt_0"))
        shutil.copyfile(os.path.join(test_dir,"small_neg_freq/mol.qout.freq_0"),os.path.join(scr_dir,"mol.qout.freq_0"))
        shutil.copyfile(os.path.join(test_dir,"small_neg_freq/mol.qout.opt_1"),os.path.join(scr_dir,"mol.qout.opt_1"))
        shutil.copyfile(os.path.join(test_dir,"small_neg_freq/mol.qout.freq_1"),os.path.join(scr_dir,"mol.qout.freq_1"))
        shutil.copyfile(os.path.join(test_dir,"small_neg_freq/mol.qout.opt_2"),os.path.join(scr_dir,"mol.qout.opt_2"))
        shutil.copyfile(os.path.join(test_dir,"small_neg_freq/mol.qout.freq_2"),os.path.join(scr_dir,"mol.qout.freq_2"))
        os.chdir(scr_dir)

    def tearDown(self):
        os.chdir(cwd)
        shutil.rmtree(scr_dir)

    def test_OptFF(self):
        myjob = QCJob.opt_with_frequency_flattener(qchem_command="qchem -slurm", max_cores=32,input_file="mol.qin", output_file="mol.qout", linked=True)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_0",
                        scratch_dir=os.getcwd(),
                        save_scratch=True,
                        save_name="chain_scratch",
                        backup=True).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_0",
                        scratch_dir=os.getcwd(),
                        save_scratch=True,
                        save_name="chain_scratch",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"small_neg_freq/mol.qin.freq_0")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_1",
                        scratch_dir=os.getcwd(),
                        save_scratch=True,
                        save_name="chain_scratch",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"small_neg_freq/mol.qin.opt_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_1",
                        scratch_dir=os.getcwd(),
                        save_scratch=True,
                        save_name="chain_scratch",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"small_neg_freq/mol.qin.freq_1")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".opt_2",
                        scratch_dir=os.getcwd(),
                        save_scratch=True,
                        save_name="chain_scratch",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"small_neg_freq/mol.qin.opt_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        expected_next = QCJob(
                        qchem_command="qchem -slurm",
                        max_cores=32,
                        multimode="openmp",
                        input_file="mol.qin",
                        output_file="mol.qout",
                        suffix=".freq_2",
                        scratch_dir=os.getcwd(),
                        save_scratch=True,
                        save_name="chain_scratch",
                        backup=False).as_dict()
        self.assertEqual(next(myjob).as_dict(),expected_next)
        self.assertEqual(QCInput.from_file(os.path.join(test_dir,"small_neg_freq/mol.qin.freq_2")).as_dict(),QCInput.from_file(os.path.join(scr_dir,"mol.qin")).as_dict())
        self.assertRaises(StopIteration,myjob.__next__)


if __name__ == "__main__":
    unittest.main()
