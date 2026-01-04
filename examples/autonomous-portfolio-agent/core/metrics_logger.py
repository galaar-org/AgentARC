"""Metrics Logger for Autonomous Portfolio Agent

Tracks and logs:
- Successful trades
- Blocked attacks (honeypots, policy violations)
- Portfolio performance
- Agent decisions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter


class MetricsLogger:
    """Logger for tracking agent metrics and blocked attacks"""

    def __init__(self, metrics_file: str = "metrics.json"):
        self.metrics_file = metrics_file
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> Dict:
        """Load existing metrics from file"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

        # Initialize empty metrics
        return {
            'start_time': datetime.now().isoformat(),
            'cycles': [],
            'trades': [],
            'blocks': [],
            'errors': []
        }

    def _save_metrics(self):
        """Save metrics to file"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save metrics: {e}")

    def log_cycle(self, cycle_num: int, analysis_result: Any):
        """Log a rebalancing cycle"""
        entry = {
            'cycle': cycle_num,
            'timestamp': datetime.now().isoformat(),
            'analysis': str(analysis_result)[:500]  # Truncate for storage
        }
        self.metrics['cycles'].append(entry)
        self._save_metrics()

    def log_trade(self, from_token: str, to_token: str, amount: str, tx_hash: str):
        """Log a successful trade"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'from_token': from_token,
            'to_token': to_token,
            'amount': amount,
            'tx_hash': tx_hash,
            'type': 'trade'
        }
        self.metrics['trades'].append(entry)
        self._save_metrics()

        print(f"✅ Trade logged: {from_token} → {to_token} ({amount})")

    def log_blocked(self, attack_type: str, reason: str, details: Dict = None):
        """Log a blocked attack/malicious transaction"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'attack_type': attack_type,
            'reason': reason,
            'details': details or {},
            'blocked': True
        }
        self.metrics['blocks'].append(entry)
        self._save_metrics()

        print(f"\n{'='*60}")
        print(f"🛡️  ATTACK BLOCKED!")
        print(f"   Type: {attack_type}")
        print(f"   Reason: {reason}")
        if details:
            print(f"   Details: {json.dumps(details, indent=6)}")
        print(f"{'='*60}\n")

    def log_error(self, error_msg: str):
        """Log an error"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'error': error_msg
        }
        self.metrics['errors'].append(entry)
        self._save_metrics()

    def get_stats(self) -> Dict:
        """Get summary statistics"""
        blocks_by_type = Counter([b['attack_type'] for b in self.metrics['blocks']])

        return {
            'start_time': self.metrics['start_time'],
            'cycles': len(self.metrics['cycles']),
            'trades': len(self.metrics['trades']),
            'blocks': len(self.metrics['blocks']),
            'errors': len(self.metrics['errors']),
            'blocks_by_type': dict(blocks_by_type),
            'recent_trades': self.metrics['trades'][-5:],  # Last 5 trades
            'recent_blocks': self.metrics['blocks'][-5:],  # Last 5 blocks
        }

    def print_summary(self):
        """Print a summary of metrics"""
        stats = self.get_stats()

        print(f"\n{'='*60}")
        print(f"📊 AGENT METRICS SUMMARY")
        print(f"{'='*60}")
        print(f"Started: {stats['start_time']}")
        print(f"Cycles run: {stats['cycles']}")
        print(f"Successful trades: {stats['trades']}")
        print(f"Blocked attacks: {stats['blocks']}")
        print(f"Errors: {stats['errors']}")

        if stats['blocks_by_type']:
            print(f"\nBlocked by type:")
            for attack_type, count in stats['blocks_by_type'].items():
                print(f"  {attack_type}: {count}")

        if stats['recent_trades']:
            print(f"\nRecent trades:")
            for trade in stats['recent_trades']:
                print(f"  {trade['timestamp']}: {trade['from_token']} → {trade['to_token']}")

        if stats['recent_blocks']:
            print(f"\nRecent blocks:")
            for block in stats['recent_blocks']:
                print(f"  {block['timestamp']}: {block['attack_type']} - {block['reason']}")

        print(f"{'='*60}\n")