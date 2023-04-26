#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Erik Anderson
# Email: erik.francis.anderson@gmail.com
# Date: 03/03/2020
"""Docstring for module __init__.py"""

# Imports - standard library
from typing import List, Optional, Callable
import re
import shutil
import os
from pathlib import Path

# Imports - 3rd party packages
import yaml

# Imports - local source
from toolbox.tool import Tool
from toolbox.utils import *
from toolbox.logger import LogLevel
from toolbox.database import Database
from dataclasses import dataclass


class UniquifyTool(Tool):
    """Basic simulation tool"""
    def __init__(self, db: Database, log: Callable[[str, LogLevel], None]):
        super(UniquifyTool, self).__init__(db, log)
        self.uni = self.get_db(self.get_namespace("UniquifyTool"))
        self.in_file = str(Path(self.uni["file"]).resolve())
        self.uni_fname = Path(self.in_file).stem + "_unique" + Path(
            self.in_file).suffix
        self.job_out_file = (Path(self.get_db("internal.job_dir")) /
                             self.uni_fname).resolve()

    def steps(self):
        return [self.uniquify, self.copy_to_dir]

    def uniquify(self):
        """Uniquifies any type of file"""
        # Call respective uniquify function
        if self.uni["file_type"] == "cdl":
            self.uniquify_cdl(self.in_file, self.job_out_file)
        else:
            self.uniquify_verilog(self.in_file, self.job_out_file)

    def uniquify_cdl(self, in_file, out_file):
        """Function for cdl uniquifying"""
        # Compile SUBCKT REGEX
        re_sub = re.compile(".SUBCKT\s(\w+)[\w\s]+")
        
        # Determine SUBCKTS
        with open(in_file, 'r') as fp:
            data = fp.read()
        
        # Figure out subckts
        m_sub = re_sub.findall(data)
        
        # Remove top name from subckt list
        try:
            m_sub.remove(self.uni["top_cell"])
        except ValueError:
            self.log(
                f'Top Cell "{self.uni["top"]}" not found as subckt in file.')
        
        # Remove ommitted cells from subckt list
        for cell in self.uni['ommitted_cells']:
            try:
                m_sub.remove(cell)
            except ValueError:
                self.log(
                    f'Ommitted Cell "{cell}" not found as subckt in file.')
        
        # Search and replace all subckt names with f"{top}_"
        for sub in m_sub:
            re_inst = re.compile(r"\b(" + sub + r")\b")
            data = re_inst.sub(self.uni["top_cell"] + r'_\1', data)
            self.log(f'Replaced "{sub}" with "{self.uni["top_cell"]}_{sub}"')
        
        # Write to new file
        with open(out_file, 'w') as fp:
            fp.write(data)
        self.log(
            f'Uniquified file at "{get_rel_path(self.job_out_file, self.get_db("internal.work_dir"))}"'
        )

    def uniquify_verilog(self, in_file, out_file):
        """Function for uniquifying verilog file"""
        # Compile SUBCKT REGEX
        re_sub = re.compile("module ([\w]+)")
        
        # Determine SUBCKTS
        with open(in_file, 'r') as fp:
            data = fp.read()
        
        # Figure out subckts
        m_sub = re_sub.findall(data)
        
        # Remove top name from subckt list
        try:
            m_sub.remove(self.uni["top_cell"])
        except ValueError:
            self.log(
                f'Top Cell "{self.uni["top"]}" not found as module in file.')
        
        # Remove ommitted cells from subckt list
        for cell in self.uni['ommitted_cells']:
            try:
                m_sub.remove(cell)
            except ValueError:
                self.log(
                    f'Ommitted Cell "{cell}" not found as module in file.')
        
        # Search and replace all subckt names with f"{top}_"
        for sub in m_sub:
            re_inst = re.compile(r"\b(" + sub + r")\b")
            data = re_inst.sub(self.uni["top_cell"] + r'_\1', data)
            self.log(f'Replaced "{sub}" with "{self.uni["top_cell"]}_{sub}"')
        
        # Write to new file
        with open(out_file, 'w') as fp:
            fp.write(data)
        self.log(
            f'Uniquified file at "{get_rel_path(self.job_out_file, self.get_db("internal.work_dir"))}"'
        )

    def copy_to_dir(self):
        try:
            out_file = (Path(self.uni["out_dir"]) / self.uni_fname).resolve()
        except:
            out_file = (Path(self.get_db("internal.work_dir")) /
                        self.uni_fname).resolve()
        shutil.copy(self.job_out_file, out_file)
        self.log(
            f'Uniquified file copied to "{get_rel_path(out_file, self.get_db("internal.work_dir"))}"'
        )
