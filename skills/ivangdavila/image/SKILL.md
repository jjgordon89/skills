---
name: Image
version: 1.0.2
description: Process, optimize, and manage images with web optimization, color management, platform specs, and e-commerce standards.
---

## Quick Reference

| Task | Load |
|------|------|
| Web optimization, formats, responsive | `web.md` |
| Color profiles, metadata, RAW, print | `photography.md` |
| Social media dimensions by platform | `social.md` |
| E-commerce/marketplace standards | `ecommerce.md` |
| ImageMagick/PIL commands | `commands.md` |

---

## Format Selection

| Content | Format | Reason |
|---------|--------|--------|
| Photos | WebP (JPEG fallback) | 25-35% smaller |
| Icons, logos | SVG | Scalable, tiny |
| Screenshots with text | PNG | Sharp edges |
| Transparency + photo | WebP or PNG-24 | Alpha support |
| Animation | WebP or MP4 | NOT GIF (5-10x larger) |

**Rule:** Never use BMP, TIFF, or uncompressed for web.

---

## File Size Budgets

- **Hero images:** MAX 200KB (ideally <150KB)
- **Content images:** MAX 100KB
- **Thumbnails:** MAX 30KB
- **Icons (raster):** MAX 5KB
- **Total page load:** MAX 1.5MB images

---

## Quality Levels

| Format | Hero | General | Thumbnails |
|--------|------|---------|------------|
| JPEG | 80-85% | 70-75% | 60-65% |
| WebP | 80-82% | 72-78% | 60-70% |

**Rule:** Below 60% = visible artifacts.

---

## Retina/HiDPI

- **2x required** for standard Retina (phones, MacBooks)
- **3x only** for iPhone Plus/Max
- A 400px displayed image needs **800px source** minimum
- 1920px hero on Retina needs **3840px source**

---

## Before Processing Checklist

- [ ] Target format determined (web vs print)
- [ ] Color profile appropriate (sRGB for web)
- [ ] Dimensions/aspect ratio defined
- [ ] Compression quality set
- [ ] Metadata handling decided (strip GPS?)
