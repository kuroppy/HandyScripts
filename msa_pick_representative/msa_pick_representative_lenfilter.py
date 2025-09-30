#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
msa_pick_representative_lenfilter.py

Minimal script to pick ONE representative sequence from an MSA FASTA,
but excludes "too short" sequences before scoring.

Policy:
  (A) Pre-filter:
      - Compute ungapped length for each sequence.
      - Drop sequences with ungapped_length < --min_len (if given).
      - Compute median ungapped length; drop sequences with
        ungapped_length < --min_len_frac * median (default 0; disabled if 0).
      If all sequences would be dropped, the filter is disabled (failsafe).

  (B) Representative selection (same as base script):
      1) Build a majority consensus per column (ignoring gaps).
      2) For each remaining sequence, compute identity to consensus
         over positions where both are non-gaps and consensus != 'X'.
      3) Representative = highest consensus identity.
         Tie-breakers: lower gap fraction, then |ungapped_length - median| smaller.

Usage:
  python msa_pick_representative_lenfilter.py --fasta alignment.faa --out rep.faa \
      --min_len 120 --min_len_frac 0.7

Requires: Biopython  (pip install biopython)
"""

import argparse
from collections import Counter
import statistics
from Bio import SeqIO

def build_consensus(seqs):
    L = max(len(s) for s in seqs)
    cons = []
    for i in range(L):
        col = [s[i] if i < len(s) else '-' for s in seqs]
        cnt = Counter([c for c in col if c != '-'])
        if not cnt:
            cons.append('-')
        else:
            top = cnt.most_common()
            if len(top) == 1 or (len(top) > 1 and top[0][1] > top[1][1]):
                cons.append(top[0][0])
            else:
                cons.append('X')
    return ''.join(cons)

def consensus_identity(seq, cons):
    matches = 0
    denom = 0
    L = min(len(seq), len(cons))
    for i in range(L):
        a = seq[i]; b = cons[i]
        if a == '-' or b == '-' or b == 'X':
            continue
        denom += 1
        if a == b:
            matches += 1
    return (matches / denom) if denom > 0 else 0.0

def gap_fraction(seq):
    if not seq: return 1.0
    return seq.count('-') / len(seq)

def pick_representative(records, min_len:int=0, min_len_frac:float=0.0):
    seqs = [str(r.seq) for r in records]
    ungapped_lens = [len(s.replace('-', '')) for s in seqs]
    median_len = statistics.median(ungapped_lens) if ungapped_lens else 0

    # Pre-filter by length
    keep_idx = []
    for i, L in enumerate(ungapped_lens):
        ok_abs = (min_len <= 0) or (L >= min_len)
        ok_rel = (min_len_frac <= 0.0) or (L >= min_len_frac * median_len)
        if ok_abs and ok_rel:
            keep_idx.append(i)

    # Failsafe: if everything would be dropped, disable the filter
    if not keep_idx:
        keep_idx = list(range(len(records)))

    seqs_kept = [seqs[i] for i in keep_idx]
    recs_kept = [records[i] for i in keep_idx]
    lens_kept = [ungapped_lens[i] for i in keep_idx]
    median_len_kept = statistics.median(lens_kept) if lens_kept else 0

    cons = build_consensus(seqs_kept)

    scores = []
    for idx, s in enumerate(seqs_kept):
        ci = consensus_identity(s, cons)
        gf = gap_fraction(s)
        len_dev = abs(lens_kept[idx] - median_len_kept)
        scores.append((ci, -1.0*gf, -1.0*len_dev, idx))
    scores.sort(reverse=True)
    rep_local_idx = scores[0][3]
    return recs_kept[rep_local_idx]

def main():
    ap = argparse.ArgumentParser(description="Pick a representative sequence from an MSA FASTA with length filtering.")
    ap.add_argument("--fasta", required=True, help="Input MSA FASTA file.")
    ap.add_argument("--out", default=None, help="Output FASTA for representative (default: stdout).")
    ap.add_argument("--min_len", type=int, default=0, help="Absolute minimum UNGAPPED length (default: 0=disabled).")
    ap.add_argument("--min_len_frac", type=float, default=0.0, help="Relative minimum fraction of median UNGAPPED length (default: 0.0=disabled).")
    args = ap.parse_args()

    records = list(SeqIO.parse(args.fasta, "fasta"))
    if not records:
        raise SystemExit("No sequences found.")

    rep = pick_representative(records, min_len=args.min_len, min_len_frac=args.min_len_frac)

    if args.out:
        with open(args.out, "w") as f:
            SeqIO.write([rep], f, "fasta")
    else:
        from Bio.SeqIO import FastaIO
        import sys
        writer = FastaIO.FastaWriter(sys.stdout, wrap=None)
        writer.write_record(rep)

if __name__ == "__main__":
    main()
