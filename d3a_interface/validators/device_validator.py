"""
Copyright 2018 Grid Singularity
This file is part of D3A.

This program is free software: you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If
not, see <http://www.gnu.org/licenses/>.
"""
from abc import ABCMeta, abstractmethod


class DeviceValidator(metaclass=ABCMeta):
    """Interface for devices' validator classes."""

    @classmethod
    def validate(cls, **kwargs):
        """Validate both rate and energy values of the device."""
        cls.validate_rate(**kwargs)
        cls.validate_energy(**kwargs)

    @classmethod
    @abstractmethod
    def validate_rate(cls, **kwargs):
        """Validate the rate values of the device."""

    @classmethod
    @abstractmethod
    def validate_energy(cls, **kwargs):
        """Validate the energy values of the device."""
