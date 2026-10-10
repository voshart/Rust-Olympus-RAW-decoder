use crate::{RawError, Result};

pub(crate) fn unpack_padded_pairs(src: &[u8], row: &mut [u16]) -> Result<()> {
    if !row.len().is_multiple_of(10) || src.len() != row.len() / 10 * 16 {
        return Err(RawError::Corrupt("ORF padded row length mismatch".into()));
    }
    for (group, out) in src.as_chunks::<16>().0.iter().zip(row.as_chunks_mut::<10>().0.iter_mut()) {
        let payload = group.get(..15).ok_or_else(|| RawError::Corrupt("short ORF packed group".into()))?;
        if group.get(15) != Some(&0) {
            return Err(RawError::Unsupported("ORF padded packing with nonzero padding".into()));
        }
        for (pair, target) in payload.as_chunks::<3>().0.iter().zip(out.as_chunks_mut::<2>().0.iter_mut()) {
            let [a, b, c] = pair;
            let [first, second] = target;
            *first = u16::from(*a) | (u16::from(*b & 15) << 8);
            *second = u16::from(*b >> 4) | (u16::from(*c) << 4);
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn literal_padded_pairs_and_invalid_padding() {
        let mut bytes = vec![0, 0xf0, 0xff, 1, 0xe0, 0xff, 0, 1, 0x80, 0, 0, 0, 0, 0, 0, 0];
        let mut output = [0; 10];
        unpack_padded_pairs(&bytes, &mut output).unwrap();
        assert_eq!(output, [0, 4095, 1, 4094, 256, 2048, 0, 0, 0, 0]);
        bytes[15] = 1;
        assert!(matches!(unpack_padded_pairs(&bytes, &mut output), Err(RawError::Unsupported(_))));
        assert!(unpack_padded_pairs(&bytes[..15], &mut output).is_err());
    }
}
