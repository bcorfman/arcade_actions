"""Tests for visualizer window closing behavior."""

from __future__ import annotations

import arcade
import pytest

from actions import Action
from actions.visualizer import attach as visualizer_attach
from actions.visualizer import detach_visualizer, get_visualizer_session


