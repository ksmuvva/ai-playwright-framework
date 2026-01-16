"""
Memory Management CLI Commands

Provides commands for querying, managing, and analyzing the memory system.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from tabulate import tabulate


@click.group()
def memory():
    """Memory management commands."""
    pass


@memory.command()
@click.argument("query")
@click.option("--type", "-t", help="Memory type to search (short_term, long_term, semantic, episodic, working)")
@click.option("--limit", "-l", default=10, help="Maximum number of results")
@click.option("--tags", "-g", help="Comma-separated list of tags to filter")
def query(query: str, type: Optional[str], limit: int, tags: Optional[str]):
    """
    Query memory for information.

    Example:
        cpa memory query "selector_healing" --tags successful --limit 5
    """
    async def _query():
        from ...skills.builtins.e10_1_memory_manager import (
            MemoryManager,
            MemoryType,
            MemoryQuery,
        )

        manager = MemoryManager(persist_to_disk=True)

        try:
            # Build query
            query_obj = MemoryQuery(limit=limit)

            if type:
                query_obj.type = MemoryType(type)

            if tags:
                query_obj.tags = tags.split(",")

            # Search memories
            results = await manager.search(query_obj)

            # Filter by query text if provided
            if query:
                results = [
                    r for r in results
                    if query.lower() in str(r.value).lower() or query.lower() in r.key.lower()
                ]

            # Display results
            if results:
                table_data = []
                for entry in results:
                    table_data.append([
                        entry.key[:50],
                        entry.type.value,
                        entry.priority.value,
                        str(entry.value)[:50] + "..." if len(str(entry.value)) > 50 else str(entry.value),
                        ", ".join(entry.tags[:3]),
                    ])

                click.echo(tabulate(
                    table_data,
                    headers=["Key", "Type", "Priority", "Value", "Tags"],
                    tablefmt="grid"
                ))
                click.echo(f"\nFound {len(results)} memories")
            else:
                click.echo("No memories found matching the query")

        finally:
            await manager.close()

    asyncio.run(_query())


@memory.command()
@click.option("--type", "-t", help="Filter by memory type")
def list(type: Optional[str]):
    """List all memories."""
    async def _list():
        from ...skills.builtins.e10_1_memory_manager import (
            MemoryManager,
            MemoryType,
            MemoryQuery,
        )

        manager = MemoryManager(persist_to_disk=True)

        try:
            query = MemoryQuery(limit=100)
            if type:
                from ...skills.builtins.e10_1_memory_manager import MemoryType
                query.type = MemoryType(type)

            results = await manager.search(query)

            # Group by type
            by_type = {}
            for entry in results:
                if entry.type.value not in by_type:
                    by_type[entry.type.value] = []
                by_type[entry.type.value].append(entry)

            # Display summary
            click.echo("\n=== Memory Summary ===\n")
            for mem_type, entries in sorted(by_type.items()):
                click.echo(f"{mem_type.upper()}: {len(entries)} memories")

            # Display detailed list
            click.echo("\n=== Detailed List ===\n")
            for entry in results:
                click.echo(f"Key: {entry.key}")
                click.echo(f"  Type: {entry.type.value}")
                click.echo(f"  Priority: {entry.priority.value}")
                click.echo(f"  Tags: {', '.join(entry.tags)}")
                click.echo(f"  Value: {str(entry.value)[:100]}")
                click.echo()

        finally:
            await manager.close()

    asyncio.run(_list())


@memory.command()
@click.argument("key")
@click.option("--type", "-t", help="Memory type")
def get(key: str, type: Optional[str]):
    """Get a specific memory by key."""
    async def _get():
        from ...skills.builtins.e10_1_memory_manager import (
            MemoryManager,
            MemoryType,
        )

        manager = MemoryManager(persist_to_disk=True)

        try:
            entry = await manager.retrieve(
                key=key,
                type=MemoryType(type) if type else None,
            )

            if entry:
                click.echo(json.dumps(entry.to_dict(), indent=2, default=str))
            else:
                click.echo(f"Memory '{key}' not found")

        finally:
            await manager.close()

    asyncio.run(_get())


@memory.command()
@click.argument("key")
@click.option("--type", "-t", help="Memory type")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def delete(key: str, type: Optional[str], confirm: bool):
    """Delete a memory by key."""
    async def _delete():
        from ...skills.builtins.e10_1_memory_manager import (
            MemoryManager,
            MemoryType,
        )

        manager = MemoryManager(persist_to_disk=True)

        try:
            if not confirm:
                if not click.confirm(f"Delete memory '{key}'?"):
                    click.echo("Cancelled")
                    return

            success = await manager.forget(
                key=key,
                type=MemoryType(type) if type else None,
            )

            if success:
                click.echo(f"Memory '{key}' deleted successfully")
            else:
                click.echo(f"Memory '{key}' not found")

        finally:
            await manager.close()

    asyncio.run(_delete())


@memory.command()
@click.option("--type", "-t", help="Memory type to clear")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def clear(type: Optional[str], confirm: bool):
    """Clear expired memories or all memories of a type."""
    async def _clear():
        from ...skills.builtins.e10_1_memory_manager import (
            MemoryManager,
            MemoryType,
        )

        manager = MemoryManager(persist_to_disk=True)

        try:
            if type:
                if not confirm:
                    if not click.confirm(f"Clear all {type} memories?"):
                        click.echo("Cancelled")
                        return

                # Clear all memories of specific type
                query = MemoryQuery(type=MemoryType(type), limit=100000)
                results = await manager.search(query)

                cleared = 0
                for entry in results:
                    if await manager.forget(entry.key, entry.type):
                        cleared += 1

                click.echo(f"Cleared {cleared} {type} memories")
            else:
                # Clear expired memories only
                cleared = await manager.clear_expired()
                click.echo(f"Cleared {cleared} expired memories")

        finally:
            await manager.close()

    asyncio.run(_clear())


@memory.command()
def stats():
    """Display memory system statistics."""
    async def _stats():
        from ...skills.builtins.e10_1_memory_manager import MemoryManager

        manager = MemoryManager(persist_to_disk=True)

        try:
            stats = manager.get_statistics()

            click.echo("\n=== Memory Statistics ===\n")

            # Overall stats
            click.echo("Total Memories:")
            click.echo(f"  {stats['total_memories']} total")
            click.echo(f"  {stats['total_stores']} stores")
            click.echo(f"  {stats['total_retrievals']} retrievals")
            click.echo()

            # By type
            click.echo("By Type:")
            click.echo(f"  Short-term: {stats['short_term_capacity']}")
            click.echo(f"  Long-term: {stats['long_term_capacity']}")
            click.echo(f"  Working: {stats['working_memory_size']}")
            click.echo(f"  Semantic: {stats['semantic_memory_size']}")
            click.echo(f"  Episodic: {stats['episodic_memory_size']}")
            click.echo()

            # Consolidations
            click.echo(f"Consolidations: {stats['consolidations']}")

        finally:
            await manager.close()

    asyncio.run(_stats())


@memory.command()
@click.argument("output", type=click.Path())
@click.option("--type", "-t", help="Memory type to export")
def export(output: str, type: Optional[str]):
    """Export memories to JSON file."""
    async def _export():
        from ...skills.builtins.e10_1_memory_manager import (
            MemoryManager,
            MemoryType,
        )

        manager = MemoryManager(persist_to_disk=True)

        try:
            count = await manager.export_memories(
                output_path=output,
                type=MemoryType(type) if type else None,
            )

            click.echo(f"Exported {count} memories to {output}")

        finally:
            await manager.close()

    asyncio.run(_export())


@memory.command()
@click.argument("input", type=click.Path(exists=True))
def import_cmd(input: str):
    """Import memories from JSON file."""
    async def _import():
        from ...skills.builtins.e10_1_memory_manager import MemoryManager

        manager = MemoryManager(persist_to_disk=True)

        try:
            count = await manager.import_memories(input_path=input)
            click.echo(f"Imported {count} memories from {input}")

        finally:
            await manager.close()

    asyncio.run(_import())


@memory.command()
def consolidate():
    """Consolidate short-term memories to long-term."""
    async def _consolidate():
        from ...skills.builtins.e10_1_memory_manager import MemoryManager

        manager = MemoryManager(persist_to_disk=True)

        try:
            count = await manager.consolidate()
            click.echo(f"Consolidated {count} memories from short-term to long-term")

        finally:
            await manager.close()

    asyncio.run(_consolidate())


@memory.command()
@click.option("--type", "-t", help="Filter by memory type")
@click.option("--limit", "-l", default=10, help="Number of recent memories")
def recent(type: Optional[str], limit: int):
    """Show recent memories."""
    async def _recent():
        from ...skills.builtins.e10_1_memory_manager import (
            MemoryManager,
            MemoryType,
        )

        manager = MemoryManager(persist_to_disk=True)

        try:
            results = await manager.recall_recent(
                count=limit,
                type=MemoryType(type) if type else None,
            )

            if results:
                table_data = []
                for entry in results:
                    table_data.append([
                        entry.accessed_at,
                        entry.type.value,
                        entry.key[:50],
                        str(entry.value)[:50] + "..." if len(str(entry.value)) > 50 else str(entry.value),
                    ])

                click.echo(tabulate(
                    table_data,
                    headers=["Accessed", "Type", "Key", "Value"],
                    tablefmt="grid"
                ))
            else:
                click.echo("No recent memories found")

        finally:
            await manager.close()

    asyncio.run(_recent())
