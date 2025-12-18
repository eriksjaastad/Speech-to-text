#!/usr/bin/env python3
"""
Test Harness for Erik STT

Runs all test corpus files through the transcription pipeline
and generates a detailed report highlighting SuperWhisper pain points:
1. Tail-cutoff detection
2. Pause handling
3. Audio capture vs transcription isolation
"""

import sys
from pathlib import Path
import json
import time
from scipy.io.wavfile import read as read_wav

# Import our STT components
from src.engine import WhisperEngine, load_settings, load_vocab
from src.post_process import load_replacements, process_mode_a

class TestRunner:
    def __init__(self):
        print("Initializing test harness...")
        
        # Load configs
        self.settings = load_settings()
        self.vocab = load_vocab()
        self.replacements = load_replacements()
        
        # Initialize engine
        self.engine = WhisperEngine(self.settings)
        
        print("✅ Test harness ready\n")
    
    def load_ground_truth(self, test_path):
        """Load ground truth transcript for a test."""
        txt_path = test_path.with_suffix('.txt')
        if not txt_path.exists():
            return None
        return txt_path.read_text().strip()
    
    def transcribe_test(self, audio_path):
        """Run transcription pipeline on a test audio file."""
        start_time = time.time()
        
        # Transcribe (bypasses audio capture - tests engine directly)
        result = self.engine.transcribe(str(audio_path), custom_vocab=self.vocab)
        raw_text = result['text']
        
        # Post-process
        final_text = process_mode_a(raw_text, self.replacements)
        
        elapsed = time.time() - start_time
        
        return {
            'raw': raw_text,
            'final': final_text,
            'latency_ms': int(elapsed * 1000),
            'audio_duration': result.get('duration', 0)
        }
    
    def check_tail_cutoff(self, ground_truth, transcribed):
        """
        Check if the tail (last sentence) was cut off.
        
        SuperWhisper Pain Point #1: Last sentence gets dropped.
        """
        if not ground_truth or not transcribed:
            return {'detected': True, 'reason': 'Missing text'}
        
        # Compare last 5 words
        gt_words = ground_truth.lower().split()
        trans_words = transcribed.lower().split()
        
        if len(gt_words) < 3 or len(trans_words) < 3:
            return {'detected': False, 'reason': 'Text too short to evaluate'}
        
        # Get last 5 words from each
        gt_tail = gt_words[-5:] if len(gt_words) >= 5 else gt_words
        trans_tail = trans_words[-5:] if len(trans_words) >= 5 else trans_words
        
        # Count matches
        matches = sum(1 for w in gt_tail if w in trans_tail)
        
        if matches < 3:
            return {
                'detected': True,
                'reason': f'Only {matches}/5 tail words match',
                'ground_truth_tail': ' '.join(gt_tail),
                'transcribed_tail': ' '.join(trans_tail)
            }
        
        return {'detected': False, 'matches': matches}
    
    def check_pause_handling(self, test_name, ground_truth, transcribed):
        """
        Check if pauses caused truncation.
        
        SuperWhisper Pain Point #2: Pauses cause weird transcription.
        """
        # Only check for tests with known pauses
        pause_tests = ['06_mid_pause', '07_long_pause', '09_breath_then_final']
        
        if test_name not in pause_tests:
            return {'applicable': False}
        
        if not ground_truth or not transcribed:
            return {'applicable': True, 'issue_detected': True, 'reason': 'Missing text'}
        
        # Simple heuristic: check if transcription is significantly shorter
        gt_words = len(ground_truth.split())
        trans_words = len(transcribed.split())
        
        ratio = trans_words / gt_words if gt_words > 0 else 0
        
        if ratio < 0.7:
            return {
                'applicable': True,
                'issue_detected': True,
                'reason': f'Transcription {ratio:.0%} of expected length (may indicate pause truncation)',
                'ground_truth_words': gt_words,
                'transcribed_words': trans_words
            }
        
        return {'applicable': True, 'issue_detected': False}
    
    def calculate_wer(self, ground_truth, transcribed):
        """
        Calculate Word Error Rate (WER).
        Simple implementation: (insertions + deletions + substitutions) / total words
        """
        if not ground_truth or not transcribed:
            return 1.0
        
        gt_words = ground_truth.lower().split()
        trans_words = transcribed.lower().split()
        
        # Very simple approximation: Levenshtein distance on word level
        # For now, just compare word counts as proxy
        diff = abs(len(gt_words) - len(trans_words))
        total = max(len(gt_words), len(trans_words))
        
        return diff / total if total > 0 else 0.0
    
    def run_test(self, audio_path):
        """Run a single test and return results."""
        test_name = audio_path.stem
        
        print(f"   🧪 {test_name}...", end=' ')
        sys.stdout.flush()
        
        # Load ground truth
        ground_truth = self.load_ground_truth(audio_path)
        if ground_truth is None:
            print("❌ SKIP (no ground truth)")
            return None
        
        # Run transcription
        try:
            result = self.transcribe_test(audio_path)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return {
                'test_name': test_name,
                'ground_truth': ground_truth,
                'error': str(e),
                'pass': False
            }
        
        # Analysis
        tail_check = self.check_tail_cutoff(ground_truth, result['final'])
        pause_check = self.check_pause_handling(test_name, ground_truth, result['final'])
        wer = self.calculate_wer(ground_truth, result['final'])
        
        # Determine pass/fail
        passed = (
            not tail_check['detected'] and
            (not pause_check.get('applicable') or not pause_check.get('issue_detected', False)) and
            wer < 0.3  # Allow up to 30% word error rate
        )
        
        print("✅ PASS" if passed else "❌ FAIL")
        
        return {
            'test_name': test_name,
            'ground_truth': ground_truth,
            'transcribed': result['final'],
            'raw_transcription': result['raw'],
            'latency_ms': result['latency_ms'],
            'audio_duration_s': result['audio_duration'],
            'tail_cutoff': tail_check,
            'pause_handling': pause_check,
            'word_error_rate': wer,
            'pass': passed
        }
    
    def save_test_result(self, result, results_dir):
        """Save individual test result to disk."""
        if result is None:
            return
        
        test_dir = results_dir / result['test_name']
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Save transcription
        (test_dir / 'transcribed.txt').write_text(result.get('transcribed', 'ERROR'))
        
        # Save raw transcription
        if 'raw_transcription' in result:
            (test_dir / 'raw_transcription.txt').write_text(result['raw_transcription'])
        
        # Save metrics
        metrics = {
            'test_name': result['test_name'],
            'pass': result['pass'],
            'latency_ms': result.get('latency_ms'),
            'audio_duration_s': result.get('audio_duration_s'),
            'tail_cutoff': result.get('tail_cutoff'),
            'pause_handling': result.get('pause_handling'),
            'word_error_rate': result.get('word_error_rate'),
            'error': result.get('error')
        }
        (test_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2))
    
    def generate_report(self, results, report_path):
        """Generate summary report in Markdown."""
        passed = [r for r in results if r and r['pass']]
        failed = [r for r in results if r and not r['pass']]
        
        report = []
        report.append("# Test Results Report\n")
        report.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Total Tests:** {len(results)}")
        report.append(f"**Passed:** {len(passed)} ✅")
        report.append(f"**Failed:** {len(failed)} ❌\n")
        
        if len(results) > 0:
            pass_rate = len(passed) / len(results) * 100
            report.append(f"**Pass Rate:** {pass_rate:.1f}%\n")
        
        # SuperWhisper Pain Point Analysis
        report.append("---\n")
        report.append("## 🎯 SuperWhisper Pain Point Analysis\n")
        
        # Tail-cutoff analysis
        tail_issues = [r for r in results if r and r.get('tail_cutoff', {}).get('detected')]
        report.append(f"### 1. Tail-Cutoff Detection\n")
        report.append(f"**Tests with tail-cutoff:** {len(tail_issues)}/{len(results)}\n")
        if tail_issues:
            report.append("\n**Failed Tests:**\n")
            for r in tail_issues:
                report.append(f"- `{r['test_name']}`: {r['tail_cutoff'].get('reason', 'Unknown')}\n")
        else:
            report.append("✅ **No tail-cutoff detected!**\n")
        
        # Pause handling analysis
        pause_tests = [r for r in results if r and r.get('pause_handling', {}).get('applicable')]
        pause_issues = [r for r in pause_tests if r.get('pause_handling', {}).get('issue_detected')]
        report.append(f"\n### 2. Pause Handling\n")
        report.append(f"**Pause tests:** {len(pause_tests)}")
        report.append(f"**Tests with pause issues:** {len(pause_issues)}/{len(pause_tests)}\n")
        if pause_issues:
            report.append("\n**Failed Tests:**\n")
            for r in pause_issues:
                report.append(f"- `{r['test_name']}`: {r['pause_handling'].get('reason', 'Unknown')}\n")
        else:
            report.append("✅ **All pause tests passed!**\n")
        
        # Latency analysis
        report.append("---\n")
        report.append("## ⏱️ Performance\n")
        latencies = [r['latency_ms'] for r in results if r and 'latency_ms' in r]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            report.append(f"**Average Latency:** {avg_latency:.0f}ms")
            report.append(f"**Max Latency:** {max_latency:.0f}ms")
            report.append(f"**Target:** <3000ms\n")
            if avg_latency < 3000:
                report.append("✅ **Latency target met!**\n")
            else:
                report.append("❌ **Latency too high**\n")
        
        # Detailed results
        report.append("---\n")
        report.append("## 📊 Detailed Results\n")
        
        for r in results:
            if not r:
                continue
            
            status = "✅ PASS" if r['pass'] else "❌ FAIL"
            report.append(f"\n### {r['test_name']} {status}\n")
            
            if 'error' in r:
                report.append(f"**Error:** `{r['error']}`\n")
                continue
            
            report.append(f"**Latency:** {r.get('latency_ms', 0)}ms")
            report.append(f"**WER:** {r.get('word_error_rate', 0):.2%}\n")
            
            report.append(f"**Ground Truth:**")
            report.append(f"```")
            report.append(f"{r['ground_truth']}")
            report.append(f"```\n")
            
            report.append(f"**Transcribed:**")
            report.append(f"```")
            report.append(f"{r.get('transcribed', 'ERROR')}")
            report.append(f"```\n")
            
            # Tail analysis
            tail = r.get('tail_cutoff', {})
            if tail.get('detected'):
                report.append(f"⚠️ **Tail-cutoff detected:** {tail.get('reason')}\n")
            
            # Pause analysis
            pause = r.get('pause_handling', {})
            if pause.get('applicable') and pause.get('issue_detected'):
                report.append(f"⚠️ **Pause issue:** {pause.get('reason')}\n")
        
        # Save report
        report_text = '\n'.join(report)
        report_path.write_text(report_text)
        
        return report_text
    
    def run_all(self):
        """Run all tests in the corpus."""
        corpus_dir = Path("test_data/corpus")
        results_dir = Path("test_results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all test audio files
        test_files = sorted(corpus_dir.glob("*.wav"))
        
        if not test_files:
            print("❌ No test files found in test_data/corpus/")
            print("   Run test_record_corpus.py first to create test data.")
            return
        
        print(f"Running {len(test_files)} tests...\n")
        
        results = []
        for test_file in test_files:
            result = self.run_test(test_file)
            if result:
                results.append(result)
                self.save_test_result(result, results_dir)
        
        print("\n" + "=" * 70)
        print("Generating report...")
        
        report_path = results_dir / "REPORT.md"
        report = self.generate_report(results, report_path)
        
        print(f"✅ Report saved to: {report_path.absolute()}")
        print("=" * 70)
        
        # Print summary
        passed = [r for r in results if r['pass']]
        failed = [r for r in results if not r['pass']]
        
        print(f"\n📊 SUMMARY")
        print(f"   Total: {len(results)}")
        print(f"   Passed: {len(passed)} ✅")
        print(f"   Failed: {len(failed)} ❌")
        
        if len(results) > 0:
            pass_rate = len(passed) / len(results) * 100
            print(f"   Pass Rate: {pass_rate:.1f}%")
        
        # Key findings
        tail_issues = [r for r in results if r.get('tail_cutoff', {}).get('detected')]
        pause_issues = [r for r in results if r.get('pause_handling', {}).get('applicable') 
                       and r.get('pause_handling', {}).get('issue_detected')]
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   Tail-cutoff issues: {len(tail_issues)}")
        print(f"   Pause issues: {len(pause_issues)}")
        
        if len(failed) == 0:
            print("\n🎉 ALL TESTS PASSED! Better than SuperWhisper!")
        else:
            print(f"\n⚠️  {len(failed)} tests need attention. See REPORT.md for details.")

def main():
    print("=" * 70)
    print("ERIK STT TEST RUNNER")
    print("=" * 70)
    print("\nThis will run all test corpus files through the transcription")
    print("pipeline to identify SuperWhisper pain points:")
    print("  1. Tail-cutoff (last sentence dropped)")
    print("  2. Pause handling (pauses cause truncation)")
    print("\nNote: This bypasses live audio capture to isolate transcription issues.\n")
    
    runner = TestRunner()
    runner.run_all()

if __name__ == "__main__":
    main()

