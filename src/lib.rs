//! Olympus ORF sensor decoding, independent of a photo editor.
//!
//! [`decode_orf`] supports the measured E01/V02 compressed 12-bit profile and
//! the measured E-M5 II padded 12-bit high-resolution layout. Other layouts
//! return an error. Samples retain the stored sensor origin and margins;
//! demosaicing, colour calibration, orientation and editing belong to callers.
#![forbid(unsafe_code)]
#![deny(clippy::unwrap_used, clippy::expect_used, clippy::panic, clippy::unimplemented, clippy::todo, clippy::unreachable)]

pub mod compressed;
mod packed;

use olympus_tiff::{ByteOrder, Ifd, Tiff, Value, makernote, tags};

/// Failure to decode a supported specimen safely.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RawError {
    Unsupported(String),
    Corrupt(String),
    Limit(&'static str),
}

impl std::fmt::Display for RawError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Unsupported(s) => write!(f, "unsupported ORF: {s}"),
            Self::Corrupt(s) => write!(f, "corrupt ORF: {s}"),
            Self::Limit(s) => write!(f, "ORF resource limit: {s}"),
        }
    }
}
impl std::error::Error for RawError {}
impl From<olympus_tiff::TiffError> for RawError {
    fn from(error: olympus_tiff::TiffError) -> Self {
        Self::Corrupt(error.to_string())
    }
}
pub type Result<T> = std::result::Result<T, RawError>;

/// Sensor-relative crop. No orientation transform has been applied.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Rect {
    pub x: usize,
    pub y: usize,
    pub width: usize,
    pub height: usize,
}

/// Uncorrected row-major sensor samples and the metadata needed to interpret them.
#[derive(Debug, Clone)]
pub struct SensorImage {
    pub width: usize,
    pub height: usize,
    pub samples: Vec<u16>,
    pub bits: u8,
    /// Four letters at the full sensor origin, e.g. `RGGB`. Shift for an odd crop.
    pub cfa: &'static str,
    pub active_area: Rect,
    /// Original Exif orientation value; pixels are not rotated.
    pub orientation: u16,
    /// Original maker-note values, not remapped to a cropped Bayer cell.
    pub black_levels: Option<[u16; 4]>,
    /// Camera red/green/blue ratios. These are not a colour calibration matrix.
    pub white_balance: Option<[f64; 3]>,
}

fn processing(bytes: &[u8], tiff: &Tiff) -> Option<Ifd> {
    let make = tiff.find(tags::MAKE).and_then(|e| e.value.as_str()).unwrap_or_default();
    let entry = tiff.exif()?.get(tags::MAKER_NOTE)?;
    let len = u64::try_from(entry.count()).ok()?;
    let note = makernote::parse_makernote(bytes, entry.offset, len, tiff.order, &make)?;
    let entry = note.ifd.get(0x2040)?;
    let offset = match &entry.value {
        Value::Undefined(_) | Value::Byte(_) => entry.offset,
        _ => note.base.checked_add(note.ifd.u64(0x2040)?)?,
    };
    let options = olympus_tiff::ParseOptions { max_ifds: 4, max_depth: 1, follow_children: false, ..Default::default() };
    olympus_tiff::parse_ifd_at(bytes, offset, note.order, note.base, false, &options).ok().map(|(ifd, _)| ifd)
}

fn cfa(tiff: &Tiff) -> Option<&'static str> {
    let &[a, b, c, d, r, s, t, u] = tiff.exif()?.bytes(0xa302)? else { return None };
    let two = |a, b| matches!((a, b), (2, 0) | (0, 2));
    if !two(a, b) || !two(c, d) {
        return None;
    }
    match [r, s, t, u] {
        [0, 1, 1, 2] => Some("RGGB"),
        [2, 1, 1, 0] => Some("BGGR"),
        [1, 0, 2, 1] => Some("GRBG"),
        [1, 2, 0, 1] => Some("GBRG"),
        _ => None,
    }
}

/// Decode one of the measured ORF layouts. Requires valid per-file Bayer metadata.
///
/// Limits: input <=512 MiB, <=96 million samples, <=16384 columns, <=20000 rows.
/// This API never silently selects a decoder for an unfamiliar coding fingerprint.
pub fn decode_orf(bytes: &[u8]) -> Result<SensorImage> {
    if bytes.len() > 512 * 1024 * 1024 {
        return Err(RawError::Limit("file exceeds 512 MiB"));
    }
    if !matches!(bytes.get(..4), Some(b"IIRO" | b"IIRS" | b"MMOR")) {
        return Err(RawError::Unsupported("not an ORF container".into()));
    }
    let tiff = Tiff::parse(bytes)?;
    let ifd = tiff.ifds.first().ok_or_else(|| RawError::Corrupt("missing IFD0".into()))?;
    let info = ifd.image()?;
    let width = usize::try_from(info.width).map_err(|_| RawError::Limit("width"))?;
    let height = usize::try_from(info.height).map_err(|_| RawError::Limit("height"))?;
    let count = width.checked_mul(height).filter(|&n| n > 0 && n <= 96_000_000).ok_or(RawError::Limit("sample budget"))?;
    if width > 16_384 || height > 20_000 {
        return Err(RawError::Limit("dimension budget"));
    }
    if tiff.order != ByteOrder::Little
        || info.samples_per_pixel != 1
        || ifd.u64(tags::SAMPLES_PER_PIXEL).is_some_and(|v| v != 1)
        || info.sample_format != 1
        || info.compression != 1
        || info.planar != 1
        || info.predictor != 1
        || info.offsets.len() != 1
        || info.byte_counts.len() != 1
        || ifd.u64(tags::ROWS_PER_STRIP) != Some(u64::from(info.height))
        || !matches!(info.layout, olympus_tiff::image::Layout::Strips { .. })
    {
        return Err(RawError::Unsupported("unverified container layout".into()));
    }
    let cfa = cfa(&tiff).ok_or_else(|| RawError::Unsupported("missing or invalid Exif Bayer pattern".into()))?;
    let offset = info.offsets.first().copied().and_then(|v| usize::try_from(v).ok()).ok_or(RawError::Limit("strip offset"))?;
    let length = info
        .byte_counts
        .first()
        .copied()
        .and_then(|v| usize::try_from(v).ok())
        .filter(|&v| v > 0)
        .ok_or_else(|| RawError::Corrupt("empty strip".into()))?;
    let end = offset.checked_add(length).ok_or(RawError::Limit("strip end"))?;
    let strip = bytes.get(offset..end).ok_or_else(|| RawError::Corrupt("strip outside file".into()))?;
    let ip = processing(bytes, &tiff);
    let samples = if ip.as_ref().is_some_and(compressed::matches_profile) {
        if info.bits_per_sample.as_slice() != [16] {
            return Err(RawError::Unsupported("unverified compressed storage depth".into()));
        }
        compressed::decode(strip, width, height)?
    } else {
        if ip.as_ref().is_some_and(compressed::has_coding_fields) {
            return Err(RawError::Unsupported("unverified coding fingerprint".into()));
        }
        let stride = width.checked_div(10).and_then(|v| v.checked_mul(16)).ok_or(RawError::Limit("padded stride"))?;
        if !width.is_multiple_of(10) || stride.checked_mul(height) != Some(strip.len()) || !matches!(info.bits_per_sample.as_slice(), [12] | [16]) {
            return Err(RawError::Unsupported("unverified packed layout".into()));
        }
        let mut samples = Vec::new();
        samples.try_reserve_exact(count).map_err(|_| RawError::Limit("sensor allocation"))?;
        samples.resize(count, 0);
        for (src, row) in strip.chunks_exact(stride).zip(samples.chunks_exact_mut(width)) {
            packed::unpack_padded_pairs(src, row)?;
        }
        samples
    };
    let active_area = match ip.as_ref().map(|ip| [0x0612, 0x0613, 0x0614, 0x0615].map(|tag| ip.u64(tag).and_then(|v| usize::try_from(v).ok()))) {
        Some([Some(x), Some(y), Some(w), Some(h)])
            if w > 0 && h > 0 && x.checked_add(w).is_some_and(|v| v <= width) && y.checked_add(h).is_some_and(|v| v <= height) =>
        {
            Rect { x, y, width: w, height: h }
        }
        _ => Rect { x: 0, y: 0, width, height },
    };
    let black_levels = ip.as_ref().and_then(|ip| ip.u64s(0x0600)).and_then(|v| {
        let [a, b, c, d] = v.as_slice() else { return None };
        Some([u16::try_from(*a).ok()?, u16::try_from(*b).ok()?, u16::try_from(*c).ok()?, u16::try_from(*d).ok()?])
    });
    let white_balance = ip.as_ref().and_then(|ip| ip.f64s(0x0100)).and_then(|v| {
        let (r, b) = (*v.first()?, *v.get(1)?);
        (r.is_finite() && b.is_finite() && r > 0.0 && b > 0.0).then_some([r / 256.0, 1.0, b / 256.0])
    });
    Ok(SensorImage {
        width,
        height,
        samples,
        bits: 12,
        cfa,
        active_area,
        orientation: ifd.u16(tags::ORIENTATION).unwrap_or(1),
        black_levels,
        white_balance,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use olympus_tiff::{IfdBuilder, ImageData, TiffWriter};
    use proptest::prelude::*;

    fn fixture(profile: bool, unknown: bool, bayer: bool) -> Vec<u8> {
        let mut image = IfdBuilder::new();
        for (tag, value) in [(tags::IMAGE_WIDTH, 4), (tags::IMAGE_LENGTH, 4)] {
            image.set(tag, Value::Long(vec![value]));
        }
        for (tag, value) in [(tags::BITS_PER_SAMPLE, 16), (tags::COMPRESSION, 1), (tags::SAMPLES_PER_PIXEL, 1), (tags::SAMPLE_FORMAT, 1)] {
            image.set(tag, Value::Short(vec![value]));
        }
        image.set(tags::MAKE, Value::Ascii("OLYMPUS".into()));
        image.set_image(ImageData::Strips {
            rows_per_strip: 4,
            strips: vec![vec![0, 0, 0, 0, 1, 0, 0, 0x18, 0x10, 0x18, 0x10, 0x10, 0x10, 0x10, 0x10, 0x96, 0x10, 0x11, 0x10, 0x10, 0x10, 0x10, 0x10]],
        });
        let mut exif = IfdBuilder::new();
        if bayer {
            exif.set(0xa302, Value::Undefined(vec![2, 0, 2, 0, 0, 1, 1, 2]));
        }
        if profile {
            let mut fields = vec![(0x0611u16, 2u32, [12, 0, 0, 0])];
            fields.extend(compressed::PROFILE.iter().map(|&(tag, value)| (tag, 1, [value as u8, (value >> 8) as u8, 0, 0])));
            if unknown {
                fields[1].2[0] = 99;
            }
            let mut note = b"OLYMPUS\0II\x03\0".to_vec();
            note.extend_from_slice(&1u16.to_le_bytes());
            note.extend_from_slice(&0x2040u16.to_le_bytes());
            note.extend_from_slice(&4u16.to_le_bytes());
            note.extend_from_slice(&1u32.to_le_bytes());
            note.extend_from_slice(&30u32.to_le_bytes());
            note.extend_from_slice(&0u32.to_le_bytes());
            note.extend_from_slice(&(fields.len() as u16).to_le_bytes());
            for (tag, count, value) in fields {
                note.extend_from_slice(&tag.to_le_bytes());
                note.extend_from_slice(&3u16.to_le_bytes());
                note.extend_from_slice(&count.to_le_bytes());
                note.extend_from_slice(&value);
            }
            note.extend_from_slice(&0u32.to_le_bytes());
            exif.set(tags::MAKER_NOTE, Value::Undefined(note));
        }
        image.set_child(tags::EXIF_IFD, exif);
        let mut bytes = TiffWriter::new(ByteOrder::Little, false).write(&[image]).unwrap();
        bytes[..4].copy_from_slice(b"IIRO");
        bytes
    }

    #[test]
    fn selects_only_verified_container_profile() {
        let bytes = fixture(true, false, true);
        let image = decode_orf(&bytes).unwrap();
        assert_eq!(image.samples, [32, 0, 64, 0, 0, 0, 0, 0, 4, 0, 34, 0, 0, 0, 0, 0]);
        for bytes in [fixture(true, true, true), fixture(false, false, true), fixture(true, false, false)] {
            assert!(matches!(decode_orf(&bytes), Err(RawError::Unsupported(_))));
        }
        let parsed = Tiff::parse(&bytes).unwrap();
        let info = parsed.ifds[0].image().unwrap();
        let required_end = (info.offsets[0] + info.byte_counts[0]) as usize;
        for length in 0..required_end {
            assert!(decode_orf(&bytes[..length]).is_err());
        }
    }

    #[test]
    fn rejects_non_orf_input() {
        assert!(matches!(decode_orf(b"II*\0"), Err(RawError::Unsupported(_))));
        assert!(decode_orf(b"IIRO").is_err());
    }

    proptest! {
        #[test]
        fn hostile_containers_return_without_panicking(bytes in prop::collection::vec(any::<u8>(), 0..4096)) {
            let _ = decode_orf(&bytes);
            let mut candidate = b"IIRO".to_vec();
            candidate.extend(bytes);
            let _ = decode_orf(&candidate);
        }
    }
}
