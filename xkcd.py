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

def get_url(index):
    return "https://www.xkcd.com/%d/" % (index)

def get_random():
    return "http://dynamic.xkcd.com/random/comic/"

