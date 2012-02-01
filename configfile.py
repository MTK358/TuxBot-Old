# TuxBot, the #linux bot. Development version.
#   Copyright (C) 2011 Colson, LinuxUser324, Krenair and Tobias "ToBeFree" Frei.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/gpl-3.0.html .

import json

class ConfigFile:
    
    def __init__(self, path):
        self.path = path
        self.reload()

    def reload(self):
        f = open(self.path, "r")
        self.contents = json.load(f)
        f.close()

        self._validate();

    def _validate(self):
        pass # TODO throw an exception if self.contents doesn't contain required fields

    def get_networks(self):
        nets = self.contents["networks"]
        for i in range(0, len(nets)):
            nets[i]["identity"] = self.contents["identities"][nets[i]["identity"]]
        return nets


