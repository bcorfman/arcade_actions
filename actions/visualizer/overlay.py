"""
Overlay UI components for ACE visualizer.

Provides inspector overlay panels, action cards, and target groups
for visualizing active actions in real-time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from actions.visualizer.instrumentation import DebugDataStore, ActionSnapshot


class ActionCard:
    """
    Display card for a single action snapshot.
    
    Shows action type, progress, tag, and status information.
    """
    
    def __init__(self, snapshot: ActionSnapshot, width: int = 300):
        """
        Initialize an action card.
        
        Args:
            snapshot: Action snapshot to display
            width: Card width in pixels
        """
        self.snapshot = snapshot
        self.width = width
        self.action_id = snapshot.action_id
        self.action_type = snapshot.action_type
    
    def get_display_text(self) -> str:
        """
        Get formatted display text for this card.
        
        Returns:
            Multi-line string with action details
        """
        lines = []
        
        # Action type and tag
        if self.snapshot.tag:
            lines.append(f"{self.snapshot.action_type} (tag: {self.snapshot.tag})")
        else:
            lines.append(self.snapshot.action_type)
        
        # Progress if available
        if self.snapshot.progress is not None:
            progress_pct = int(self.snapshot.progress * 100)
            lines.append(f"  progress: {progress_pct}%")
        
        # Status indicators
        status_parts = []
        if self.snapshot.is_paused:
            status_parts.append("PAUSED")
        if self.snapshot.factor != 1.0:
            status_parts.append(f"factor: {self.snapshot.factor:.1f}")
        
        if status_parts:
            lines.append(f"  {', '.join(status_parts)}")
        
        return "\n".join(lines)
    
    def get_progress_bar_width(self) -> int:
        """
        Calculate progress bar width in pixels.
        
        Returns:
            Width of progress bar (0 if no progress available)
        """
        if self.snapshot.progress is None:
            return 0
        return int(self.width * self.snapshot.progress)


class TargetGroup:
    """
    Container for action cards grouped by target sprite/list.
    
    Groups actions that operate on the same target for better organization.
    """
    
    def __init__(self, target_id: int, target_type: str):
        """
        Initialize a target group.
        
        Args:
            target_id: ID of the target sprite/list
            target_type: Type name of the target
        """
        self.target_id = target_id
        self.target_type = target_type
        self.cards: list[ActionCard] = []
    
    def add_card(self, card: ActionCard) -> None:
        """Add an action card to this group."""
        self.cards.append(card)
    
    def get_header_text(self) -> str:
        """
        Get formatted header text for this group.
        
        Returns:
            Header string with target information
        """
        action_count = len(self.cards)
        return f"{self.target_type} (id: {self.target_id}) - {action_count} action(s)"


class InspectorOverlay:
    """
    Main inspector overlay panel.
    
    Displays grouped action cards with real-time updates from the debug store.
    Follows dependency injection by receiving the debug store as a parameter.
    """
    
    def __init__(
        self,
        debug_store: DebugDataStore,
        x: int = 10,
        y: int = 10,
        width: int = 400,
        visible: bool = True,
        filter_tag: str | None = None,
    ):
        """
        Initialize the inspector overlay.
        
        Args:
            debug_store: Injected DebugDataStore dependency
            x: X position of overlay
            y: Y position of overlay
            width: Width of overlay panel
            visible: Initial visibility state
            filter_tag: Optional tag to filter actions by
        """
        self.debug_store = debug_store
        self.x = x
        self.y = y
        self.width = width
        self.visible = visible
        self.filter_tag = filter_tag
        self.groups: list[TargetGroup] = []
        self.highlighted_target_id: int | None = None
        self._highlight_index: int = -1
    
    def toggle(self) -> None:
        """Toggle overlay visibility."""
        self.visible = not self.visible
    
    def update(self) -> None:
        """
        Update overlay from debug store data.
        
        Rebuilds target groups and action cards from current snapshots.
        """
        if not self.visible:
            self.groups = []
            return
        
        # Get all snapshots from store
        snapshots = self.debug_store.get_all_snapshots()
        
        # Apply tag filter if specified
        if self.filter_tag:
            snapshots = [s for s in snapshots if s.tag == self.filter_tag]
        
        # Group snapshots by target_id
        groups_dict: dict[int, TargetGroup] = {}
        
        for snapshot in snapshots:
            target_id = snapshot.target_id
            
            if target_id not in groups_dict:
                groups_dict[target_id] = TargetGroup(
                    target_id=target_id,
                    target_type=snapshot.target_type,
                )
            
            card = ActionCard(snapshot, width=self.width - 20)
            groups_dict[target_id].add_card(card)
        
        # Convert to list and sort by target_id for consistent ordering
        target_ids = sorted(groups_dict.keys())
        self.groups = [groups_dict[tid] for tid in target_ids]

        if not self.groups:
            self.clear_highlight()
        elif self.highlighted_target_id in target_ids:
            self._highlight_index = target_ids.index(self.highlighted_target_id)
        else:
            self.clear_highlight()
    
    def get_total_action_count(self) -> int:
        """Get total number of actions across all groups."""
        return sum(len(group.cards) for group in self.groups)

    def clear_highlight(self) -> None:
        """Clear any highlighted target."""
        self.highlighted_target_id = None
        self._highlight_index = -1

    def highlight_next(self) -> None:
        """Highlight the next target group."""
        self._cycle_highlight(direction=1)

    def highlight_previous(self) -> None:
        """Highlight the previous target group."""
        self._cycle_highlight(direction=-1)

    def _cycle_highlight(self, direction: int) -> None:
        """Cycle highlight forwards or backwards."""
        if not self.groups:
            self.clear_highlight()
            return

        target_ids = [group.target_id for group in self.groups]
        if self.highlighted_target_id in target_ids:
            current_index = target_ids.index(self.highlighted_target_id)
        else:
            current_index = -1

        if current_index == -1:
            next_index = 0 if direction > 0 else len(target_ids) - 1
        else:
            next_index = (current_index + direction) % len(target_ids)

        self._highlight_index = next_index
        self.highlighted_target_id = target_ids[next_index]

    def get_highlighted_group(self) -> TargetGroup | None:
        """Return the currently highlighted group, if any."""
        if self.highlighted_target_id is None:
            return None
        for group in self.groups:
            if group.target_id == self.highlighted_target_id:
                return group
        return None

