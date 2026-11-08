#!/usr/bin/env python3
"""把扫描版 PDF 逐页 OCR 成结构化条目（jsonl）。

用法:
    python ocr_pdf.py <pdf> <out_dir> [--dpi 200] [--from 1] [--to 106]

每页输出 out_dir/pNNN.json:
    {"page": 11, "w": 1654.0, "h": 2339.0,
     "items": [[y, x0, x1, text, score], ...]}   # 已按 y,x 排序

依赖: pymupdf、rapidocr-onnxruntime（离线中文 OCR，onnxruntime 后端）
安装（本机已验证）:
    python -m pip install --no-deps pymupdf rapidocr-onnxruntime opencv-python pyclipper Shapely PyYAML
    # 注意: 必须 --no-deps，否则 pip 会尝试升级 onnxruntime 并在长路径上报 OSError
"""
import argparse
import json
import os
import sys
import time

import pymupdf
from rapidocr_onnxruntime import RapidOCR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out_dir")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--from", dest="p_from", type=int, default=1)
    ap.add_argument("--to", dest="p_to", type=int, default=0)
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    doc = pymupdf.open(a.pdf)
    last = a.p_to or doc.page_count
    engine = RapidOCR()
    t_start = time.time()
    for pno in range(a.p_from, min(last, doc.page_count) + 1):
        out = os.path.join(a.out_dir, f"p{pno:03d}.json")
        if os.path.exists(out):
            print(f"skip p{pno}"); continue
        page = doc[pno - 1]
        pix = page.get_pixmap(dpi=a.dpi)
        tmp = os.path.join(a.out_dir, f"_tmp_p{pno:03d}.png")
        pix.save(tmp)
        t0 = time.time()
        res, _ = engine(tmp)
        items = []
        for box, text, score in (res or []):
            ys = [p[1] for p in box]; xs = [p[0] for p in box]
            items.append([round(min(ys), 1), round(min(xs), 1), round(max(xs), 1), text, round(float(score), 2)])
        items.sort(key=lambda r: (r[0], r[1]))
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"page": pno, "w": pix.width, "h": pix.height, "items": items}, f, ensure_ascii=False)
        try:
            os.remove(tmp)
        except OSError:
            pass
        print(f"p{pno:3d} items={len(items):3d} {round(time.time() - t0, 1)}s", flush=True)
    print(f"DONE {round(time.time() - t_start)}s -> {a.out_dir}")


if __name__ == "__main__":
    main()
