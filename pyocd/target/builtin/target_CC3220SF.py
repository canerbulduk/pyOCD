# pyOCD debugger
# Copyright (c) 2018-2019 Arm Limited
# Copyright (c) 2021 Chris Reed
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import time

from ...flash.flash import Flash
from ...coresight.coresight_target import CoreSightTarget
from ...core.memory_map import (RomRegion, FlashRegion, RamRegion, MemoryMap)

LOG = logging.getLogger(__name__)

FLASH_ALGO = { 'load_address' : 0x20000000,
               'instructions' : [
                                0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,
                                0xd1fd3801, 0x49964770, 0x6e48b418, 0x0000f440, 0x4b946648, 0xf241681a, 0x380140d5, 0xf042d1fd,
                                0x60180010, 0x40d5f241, 0xd1fd3801, 0xf8d24a8e, 0xf040016c, 0xf8c2003c, 0x4b8c016c, 0xf0406c98,
                                0x64980001, 0x6480f44f, 0x6cd86820, 0x0001f040, 0xf04f64d8, 0xf8cd0c00, 0x9800c000, 0x90001c40,
                                0xd3fa2810, 0xf0206cd8, 0x64d80001, 0xf0206c98, 0x64980001, 0x68c0487e, 0x0ffff010, 0x487dd106,
                                0xc000f8c0, 0x40d5f241, 0xd1fd3801, 0x00c8f8d1, 0x2802b2c0, 0xf8d2d113, 0xf0200110, 0xf420000f,
                                0xf0406040, 0xf8c20002, 0xf8d20110, 0xf0200114, 0xf420000f, 0xf0406040, 0xf8c20002, 0xf8d20114,
                                0xf0400184, 0xf8c20002, 0x486b0184, 0xf3c06800, 0x280e5083, 0x00b0f8d1, 0x007cf420, 0xf440bf0c,
                                0xf4400048, 0xf8c10024, 0x486400b0, 0xf0236803, 0x60035380, 0xb2806820, 0xd2062802, 0x00a8f8d1,
                                0x0004f040, 0x00a8f8c1, 0x6820e022, 0xd01f0c00, 0x0188f8d2, 0x00e1f040, 0x0188f8c2, 0x68034858,
                                0x0f01f013, 0x6803d014, 0x0301f023, 0xf8d26003, 0xf4400188, 0xf8c27000, 0x48520188, 0xf0226802,
                                0x60020201, 0xf8c01d00, 0x1d00c000, 0xc000f8c0, 0x6800484d, 0xf3c00f02, 0x2a036003, 0xd22cd00f,
                                0x6800484a, 0x1080f3c0, 0x6a88b158, 0x0080f020, 0x69086288, 0x4070f020, 0x5080f040, 0xb9e0e01c,
                                0x6a48e7ee, 0x000ff020, 0x6070f420, 0x30c0f420, 0x0001f040, 0x60a0f440, 0x3080f440, 0x6a886248,
                                0x0080f020, 0x4070f020, 0x007ff420, 0x104cf440, 0x69086288, 0x4070f020, 0xbc186108, 0x0000f04f,
                                0x20004770, 0x48324770, 0x2201f640, 0x49316142, 0x68816081, 0x0f04f011, 0x68c0d1fb, 0xbf184010,
                                0x47702001, 0x2201f640, 0x614a4929, 0x482a6008, 0x68886088, 0x0f02f010, 0x68c8d1fb, 0xbf184010,
                                0x47702001, 0xf242b430, 0x4b216c01, 0xc014f8c3, 0xbf182900, 0xc084f8df, 0xf020d01e, 0x601c047f,
                                0xf000e00b, 0xf105057c, 0xf5054580, 0xf852257d, 0xf8c54b04, 0x1d004100, 0xf0101f09, 0xd1010f7c,
                                0xb90c6b1c, 0xd1ec2900, 0xc020f8c3, 0xf0146a1c, 0xd1fb0f01, 0xd1e02900, 0x2000bc30, 0x00004770,
                                0x4402f000, 0x4402fc18, 0x4402e000, 0x44025000, 0x4402d000, 0x4402f804, 0x4402dc78, 0x4402fc74,
                                0x4402fc20, 0x4402f818, 0x4402dc80, 0x4402f840, 0x400fd000, 0xa4420004, 0xa4420002, 0xa4420001,
                                0x00000004, 0x00000008, 0x00000014, 0x00000018, 0x00000024, 0x00000028, 0x00000030, 0x00000034,
                                0x00000040, 0x00000044, 0x00000048, 0x0000004c, 0x00000050, 0x00000054, 0x00000058, 0x0000005c,
                                0x00000060, 0x00000064, 0x00000068, 0x0000006c, 0x00000070, 0x00000074, 0x00000078, 0x0000007c,
                                0x00000080, 0x00000084, 0x00000088, 0x0000008c, 0x00000090, 0x00000094, 0x00000098, 0x0000009c,
                                0x000000a0, 0x000000a4, 0x000000a8, 0x000000ac, 0x000000b8, 0x000000bc, 0x000000c8, 0x000000cc,
                                0x000000d8, 0x000000dc, 0x00000000, ],
               'pc_init'          : 0x20000027,
               'pc_eraseAll'      : 0x200001e7,
               'pc_erase_sector'  : 0x20000205,
               'pc_program_page'  : 0x20000225,
               'begin_data'       : 0x20002000, # Analyzer uses a max of 1 KB data (256 pages * 4 bytes / page)
               'page_buffers'    : [0x20002000, 0x20004000],   # Enable double buffering
               'begin_stack'      : 0x20000800,
               'static_base'      : 0x20000368,
               'min_program_length' : 4,
               'analyzer_supported' : False,
               'analyzer_address' : 0x20003000  # Analyzer 0x20003000..0x20003600
              }


class Flash_cc3220sf(Flash):

    def __init__(self, target):
        super(Flash_cc3220sf, self).__init__(target, FLASH_ALGO)

    def init(self):
        """
        Download the flash algorithm in RAM
        """

        self.target.halt()
        self.target.reset_and_halt()

        # update core register to execute the init subroutine

        result = self._call_function_and_wait(self.flash_algo['pc_init'], init=True)

        # check the return code
        if result != 0:
            LOG.error('init error: %i', result)

        # erase the cookie which take up one page
        self.erase_sector(0x01000000)
        time.sleep(.5)

        #do a hardware reset which will put the pc looping in rom
        self.target.dp.reset()
        time.sleep(1.3)

        # reconnect to the board
        self.target.dp.connect()

        self.target.halt()
        self.target.reset_and_halt()

        # update core register to execute the init subroutine
        result = self._call_function_and_wait(self.flash_algo['pc_init'], init=True)

        # check the return code
        if result != 0:
            LOG.error('init error: %i', result)


class CC3220SF(CoreSightTarget):
    VENDOR = "Texas Instruments"
    
    MEMORY_MAP = MemoryMap(
        RomRegion(start=0x00000000, length=0x00080000),
        FlashRegion(start=0x01000000, length=0x00100000, blocksize=0x800, is_boot_memory=True, flash_class=Flash_cc3220sf),
        RamRegion(start=0x20000000, length=0x40000)
    )

    def __init__(self, session):
        super(CC3220SF, self).__init__(session, self.MEMORY_MAP)

    def post_connect_hook(self):
        self.cores[0].default_reset_type = self.ResetType.SW_VECTRESET
        
