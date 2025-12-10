#!/usr/bin/env python3
"""
Cache & Memory Hierarchy Simulator
- Supports replacement policies: LRU, FIFO, Random, LFU
- Performs sweeps over cache size, associativity, block size
- Reports per-cache and overall stats: hits, misses, hit_ratio, miss_ratio, AMAT, total_access_time
- Exports CSV results for plotting/analysis
"""

import math
import random
import time
import csv
from typing import List, Dict, Any, Optional

# ---------------------------
# Core cache components
# ---------------------------

class CacheLine:
    """Represents a single line within a cache set."""
    def __init__(self):
        self.valid: bool = False
        self.tag: Optional[int] = None
        self.timestamp: int = 0    # used for LRU/FIFO (time loaded or last used)
        self.freq: int = 0         # used for LFU


class Cache:
    """
    A configurable cache model.
    Supports replacement policies: "LRU", "FIFO", "Random", "LFU".
    """
    def __init__(self, name: str, size: int, associativity: int, block_size: int,
                 replacement_policy: str = "LRU", hit_time: int = 1):
        # Validate inputs
        if size <= 0 or block_size <= 0 or associativity <= 0:
            raise ValueError("size, block_size, and associativity must be positive integers")
        if size % (associativity * block_size) != 0:
            raise ValueError("Cache size must be divisible by (associativity * block_size)")

        self.name = name
        self.size = size
        self.associativity = associativity
        self.block_size = block_size
        self.replacement_policy = replacement_policy
        self.hit_time = hit_time

        self.num_sets = size // (associativity * block_size)
        self.offset_bits = int(math.log2(block_size))
        self.index_bits = int(math.log2(self.num_sets)) if self.num_sets > 0 else 0
        self.tag_bits = 32 - self.index_bits - self.offset_bits

        # initialize sets & lines
        self.sets: List[List[CacheLine]] = [[CacheLine() for _ in range(associativity)] for _ in range(self.num_sets)]

        # stats
        self.hits: int = 0
        self.misses: int = 0
        self.access_count: int = 0

    def _get_address_parts(self, address: int):
        offset = address & ((1 << self.offset_bits) - 1)
        index = (address >> self.offset_bits) & ((1 << self.index_bits) - 1) if self.index_bits > 0 else 0
        tag = address >> (self.offset_bits + self.index_bits)
        return tag, index, offset

    def access(self, address: int, current_time: int) -> bool:
        """
        Access the cache with the given 32-bit address.
        Returns True on hit, False on miss.
        Updates per-line metadata depending on replacement policy.
        """
        tag, index, _ = self._get_address_parts(address)
        self.access_count += 1
        target_set = self.sets[index]

        # Search for hit
        for line in target_set:
            if line.valid and line.tag == tag:
                self.hits += 1
                # Update metadata depending on policy
                if self.replacement_policy == "LRU":
                    line.timestamp = current_time  # most recent access
                if self.replacement_policy == "LFU":
                    line.freq += 1
                # FIFO: do NOT update timestamp on hit
                return True

        # Miss: find victim to fill
        self.misses += 1
        victim_line = self._find_victim_line(target_set)
        # fill victim
        victim_line.valid = True
        victim_line.tag = tag
        # for FIFO we set timestamp when line is inserted and we don't change it on hits
        victim_line.timestamp = current_time
        # reset/initialize frequency for LFU
        victim_line.freq = 1
        return False

    def _find_victim_line(self, target_set: List[CacheLine]) -> CacheLine:
        # first try an invalid (empty) line
        for line in target_set:
            if not line.valid:
                return line

        # If no invalid line, pick according to replacement policy
        if self.replacement_policy == "Random":
            return random.choice(target_set)
        elif self.replacement_policy == "LFU":
            # pick least frequently used; tie-breaker oldest timestamp
            return min(target_set, key=lambda line: (line.freq, line.timestamp))
        elif self.replacement_policy == "FIFO":
            # pick smallest timestamp (time loaded)
            return min(target_set, key=lambda line: line.timestamp)
        else:
            # Default to LRU
            return min(target_set, key=lambda line: line.timestamp)

    def reset_stats(self):
        self.hits = 0
        self.misses = 0
        self.access_count = 0
        # reset lines
        for s in self.sets:
            for line in s:
                line.valid = False
                line.tag = None
                line.timestamp = 0
                line.freq = 0

    def get_stats_for_print(self) -> Dict[str, Any]:
        hit_ratio = self.hits / self.access_count if self.access_count > 0 else 0.0
        miss_ratio = self.misses / self.access_count if self.access_count > 0 else 0.0
        return {
            "name": self.name,
            "hits": self.hits,
            "misses": self.misses,
            "accesses": self.access_count,
            "hit_ratio": f"{hit_ratio:.2%}",
            "miss_ratio": f"{miss_ratio:.2%}",
            "hit_ratio_raw": hit_ratio,
            "miss_ratio_raw": miss_ratio,
            "num_sets": self.num_sets,
            "associativity": self.associativity,
            "block_size": self.block_size,
        }

    def get_raw_stats(self) -> Dict[str, float]:
        hit_ratio = self.hits / self.access_count if self.access_count > 0 else 0.0
        return {"name": self.name, "hit_ratio": hit_ratio, "hits": self.hits, "misses": self.misses, "accesses": self.access_count}


# ---------------------------
# Memory hierarchy
# ---------------------------

class MemoryHierarchy:
    def __init__(self, caches: List[Cache], main_memory_access_time: int = 100):
        # sort caches by hit_time ascending (fastest first)
        self.caches: List[Cache] = sorted(caches, key=lambda c: c.hit_time)
        self.main_memory_access_time = main_memory_access_time
        self.total_access_time: int = 0
        self.time_counter: int = 0  # used to timestamp accesses (for LRU/FIFO)

    def access(self, address: int):
        """
        Access an address through the cache hierarchy. Updates total_access_time and caches' counters.
        """
        self.time_counter += 1
        for cache in self.caches:
            # add cache access time to total regardless of hit/miss (probe time)
            self.total_access_time += cache.hit_time
            hit = cache.access(address, self.time_counter)
            if hit:
                return  # hit stops the search
        # Miss in all caches -> main memory access
        self.total_access_time += self.main_memory_access_time

    def reset(self):
        self.total_access_time = 0
        self.time_counter = 0
        for cache in self.caches:
            cache.reset_stats()

    def get_stats(self) -> List[Dict[str, Any]]:
        if not self.caches:
            return []
        l1_cache = self.caches[0]
        total_accesses = l1_cache.access_count
        if total_accesses == 0:
            amat = 0.0
        else:
            amat = self.total_access_time / total_accesses
        all_stats = [cache.get_stats_for_print() for cache in self.caches]
        all_stats.append({
            "name": "Overall Hierarchy",
            "Average Memory Access Time (AMAT)": f"{amat:.4f} time units",
            "Total Execution Time": f"{self.total_access_time} time units",
            "total_accesses": total_accesses
        })
        return all_stats

# ---------------------------
# Simulation runner & experiment helpers
# ---------------------------

def run_simulation(config_name: str, caches: List[Cache], memory_trace: List[int],
                   main_memory_time: int = 100, verbose: bool = True) -> Dict[str, Any]:
    """
    Runs a single simulation and returns raw metrics:
    { config_name, per_cache_stats, overall_amat, total_access_time, runtime_seconds }
    """
    if verbose:
        print(f"\n--- Running Simulation: {config_name} ---")
    start_time = time.time()

    hierarchy = MemoryHierarchy(caches, main_memory_time)
    hierarchy.reset()

    for addr in memory_trace:
        hierarchy.access(addr)

    end_time = time.time()

    stats = hierarchy.get_stats()
    if verbose:
        for stat_block in stats:
            print(f"\n--- Stats for {stat_block['name']} ---")
            for key, value in stat_block.items():
                if key != 'name':
                    print(f"{key}: {value}")

        print(f"\nSimulation wall-clock time: {end_time - start_time:.4f} seconds.")
        print("-" * (len(config_name) + 28))

    # Collect raw data for CSV / further processing
    raw_per_cache = [c.get_raw_stats() for c in hierarchy.caches]
    l1_accesses = hierarchy.caches[0].access_count if hierarchy.caches else 0
    amat = hierarchy.total_access_time / l1_accesses if l1_accesses > 0 else 0.0
    total_time = hierarchy.total_access_time

    return {
        "config_name": config_name,
        "per_cache": raw_per_cache,
        "amat": amat,
        "total_access_time": total_time,
        "wallclock_seconds": end_time - start_time,
        "l1_accesses": l1_accesses
    }


# ---------------------------
# Utility: trace generators
# ---------------------------

def generate_synthetic_trace() -> List[int]:
    """
    Recreates your original synthetic memory trace:
     - some sequential ranges
     - a chunk of random addresses
     - another sequential region
    addresses are word-addressed multiplied by 4 (byte addresses)
    """
    memory_trace = []
    for _ in range(4):
        for i in range(128):
            memory_trace.append(i * 4)
    for _ in range(256):
        memory_trace.append(random.randint(0, 4096) * 4)
    for _ in range(4):
        for i in range(2048, 2048 + 128):
            memory_trace.append(i * 4)
    return memory_trace


# ---------------------------
# Experiment suites (sweeps)
# ---------------------------

def sweep_associativity(base_cache_size: int, block_size: int, associativities: List[int], memory_trace: List[int]):
    results = []
    for assoc in associativities:
        name = f"Associativity {assoc}-way (size={base_cache_size}B, block={block_size}B)"
        cache = Cache("L1", base_cache_size, assoc, block_size, replacement_policy="LRU", hit_time=1)
        res = run_simulation(name, [cache], memory_trace, main_memory_time=100, verbose=False)
        hit_ratio = res['per_cache'][0]['hit_ratio'] if res['per_cache'] else 0.0
        results.append({"associativity": assoc, "hit_ratio": hit_ratio, "amat": res['amat']})
    return results


def sweep_block_sizes(cache_size: int, associativity: int, block_sizes: List[int], memory_trace: List[int]):
    results = []
    for block in block_sizes:
        name = f"BlockSize {block}B (size={cache_size}B, assoc={associativity})"
        cache = Cache("L1", cache_size, associativity, block, replacement_policy="LRU", hit_time=1)
        res = run_simulation(name, [cache], memory_trace, main_memory_time=100, verbose=False)
        hit_ratio = res['per_cache'][0]['hit_ratio'] if res['per_cache'] else 0.0
        results.append({"block_size": block, "hit_ratio": hit_ratio, "amat": res['amat']})
    return results


def sweep_cache_sizes(block_size: int, associativity: int, cache_sizes: List[int], memory_trace: List[int]):
    results = []
    for size in cache_sizes:
        name = f"CacheSize {size}B (block={block_size}B, assoc={associativity})"
        cache = Cache("L1", size, associativity, block_size, replacement_policy="LRU", hit_time=1)
        res = run_simulation(name, [cache], memory_trace, main_memory_time=100, verbose=False)
        hit_ratio = res['per_cache'][0]['hit_ratio'] if res['per_cache'] else 0.0
        results.append({"cache_size": size, "hit_ratio": hit_ratio, "amat": res['amat']})
    return results


# ---------------------------
# CSV helpers
# ---------------------------

def write_csv(filename: str, fieldnames: List[str], rows: List[Dict[str, Any]]):
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exported {len(rows)} rows to {filename}")


# ---------------------------
# Example main: runs several experiments and exports CSVs
# ---------------------------

def main():
    random.seed(42)
    memory_trace = generate_synthetic_trace()
    print(f"Generated memory trace with {len(memory_trace)} accesses.")

    # --- Basic configs to compare replacement policies and levels ---
    comparison_results = []

    # 1-level direct-mapped
    l1_direct = Cache("L1 (Direct)", 1024, 1, 32, replacement_policy="LRU", hit_time=1)
    comparison_results.append(run_simulation("1-Level Direct-Mapped (LRU semantics)", [l1_direct], memory_trace))

    # 1-level 4-way
    l1_4way = Cache("L1 (4-way)", 1024, 4, 32, replacement_policy="LRU", hit_time=1)
    comparison_results.append(run_simulation("1-Level 4-Way (LRU)", [l1_4way], memory_trace))

    # 2-level
    l1 = Cache("L1", 512, 2, 32, replacement_policy="LRU", hit_time=1)
    l2 = Cache("L2", 4096, 4, 64, replacement_policy="LRU", hit_time=10)
    comparison_results.append(run_simulation("2-Level (L1+L2)", [l1, l2], memory_trace))

    # Block size tests
    l1_small_block = Cache("L1 (16B blocks)", 1024, 2, 16, replacement_policy="LRU", hit_time=1)
    comparison_results.append(run_simulation("1-Level 16B Blocks", [l1_small_block], memory_trace))

    l1_large_block = Cache("L1 (64B blocks)", 1024, 2, 64, replacement_policy="LRU", hit_time=1)
    comparison_results.append(run_simulation("1-Level 64B Blocks", [l1_large_block], memory_trace))

    # Export summary CSV (one row per experiment)
    csv_rows = []
    for r in comparison_results:
        row = {
            "config_name": r["config_name"],
            "amat": r["amat"],
            "total_access_time": r["total_access_time"],
            "wallclock_seconds": r["wallclock_seconds"],
            "l1_hit_ratio": r["per_cache"][0]["hit_ratio"] if r["per_cache"] else 0.0
        }
        csv_rows.append(row)

    write_csv('simulation_comparison.csv', ['config_name', 'amat', 'total_access_time', 'wallclock_seconds', 'l1_hit_ratio'], csv_rows)

    # --- Associativity sweep example ---
    associativity_levels = [1, 2, 4, 8, 16]
    assoc_results = sweep_associativity(base_cache_size=2048, block_size=64, associativities=associativity_levels, memory_trace=memory_trace)
    write_csv('associativity_analysis.csv', ['associativity', 'hit_ratio', 'amat'], assoc_results)

    # --- Block-size sweep example ---
    block_sizes = [8, 16, 32, 64, 128]
    block_results = sweep_block_sizes(cache_size=1024, associativity=2, block_sizes=block_sizes, memory_trace=memory_trace)
    write_csv('blocksize_analysis.csv', ['block_size', 'hit_ratio', 'amat'], block_results)

    # --- Replacement-policy comparison example ---
    policies = ["LRU", "FIFO", "Random", "LFU"]
    policy_rows = []
    for policy in policies:
        c = Cache("L1", 1024, 4, 32, replacement_policy=policy, hit_time=1)
        res = run_simulation(f"Policy {policy}", [c], memory_trace, main_memory_time=100, verbose=False)
        hit_ratio = res['per_cache'][0]['hit_ratio'] if res['per_cache'] else 0.0
        policy_rows.append({"policy": policy, "hit_ratio": hit_ratio, "amat": res['amat']})
    write_csv('policy_comparison.csv', ['policy', 'hit_ratio', 'amat'], policy_rows)

    print("All example experiments finished. CSV files created for analysis.")


if __name__ == "__main__":
    main()
