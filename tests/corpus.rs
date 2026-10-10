//! Explicitly requested, full-sensor replay of the recorded compressed results.
use sha2::{Digest, Sha256};
use std::path::Path;

#[test]
#[ignore = "requires Git LFS creator media and fetched CC0 external corpus"]
fn compressed_full_sensor_hashes() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let report: serde_json::Value = serde_json::from_str(include_str!("../research/results/compressed-full-frame-summary.json")).unwrap();
    let mut count = 0;
    let mut sample_count = 0;
    for case in report["cases"].as_array().unwrap() {
        let name = case["file"].as_str().unwrap();
        let folder = if name.starts_with("pixls-") { "corpus/external" } else { "corpus/voshart-olympus" };
        let bytes = std::fs::read(root.join(folder).join(name)).unwrap();
        assert_eq!(format!("{:x}", Sha256::digest(&bytes)), case["input_sha256"].as_str().unwrap(), "{name}: original identity");
        let image = olympus_raw::decode_orf(&bytes).unwrap_or_else(|error| panic!("{name}: {error}"));
        assert_eq!(image.width as u64, case["sensor"][0].as_u64().unwrap(), "{name}");
        assert_eq!(image.height as u64, case["sensor"][1].as_u64().unwrap(), "{name}");
        assert_eq!(image.cfa, case["cfa"].as_str().unwrap(), "{name}");
        assert_eq!(image.bits, 12);
        let expected_crop = &case["image_processing"];
        if let (Some(x), Some(y), Some(w), Some(h)) = (
            expected_crop["crop_left"][0].as_u64(),
            expected_crop["crop_top"][0].as_u64(),
            expected_crop["crop_width"][0].as_u64(),
            expected_crop["crop_height"][0].as_u64(),
        ) {
            assert_eq!(image.active_area, olympus_raw::Rect { x: x as usize, y: y as usize, width: w as usize, height: h as usize }, "{name}: crop");
        }
        let mut hash = Sha256::new();
        for chunk in image.samples.chunks(8192) {
            let bytes: Vec<u8> = chunk.iter().flat_map(|v| v.to_le_bytes()).collect();
            hash.update(bytes);
        }
        assert_eq!(format!("{:x}", hash.finalize()), case["sensor_sha256_le_u16"].as_str().unwrap(), "{name}: complete sensor");
        sample_count += image.samples.len();
        count += 1;
    }
    assert_eq!(count, 17);
    assert_eq!(sample_count, 434_555_200);
    eprintln!("Matched {count} complete compressed rasters / {sample_count} samples.");
}

#[test]
#[ignore = "requires Git LFS creator media and fetched pixls-2856.ORF"]
fn padded_full_sensor_hashes() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    for (path, input_hash, sensor_hash) in [
        (
            "corpus/voshart-olympus/PA280725_EM5MkII_Lumix G Fisheye 8mmF3.5.ORF",
            "922ee554fa21f21f0598131dae1fc95adfcda61f090c3991e0f6a0997a55a2c2",
            "aea032c10a27ff82918a465b4cc0bdb701f65ce119a3d134ad8ebd60ff5d61d3",
        ),
        (
            "corpus/external/pixls-2856.ORF",
            "5c42fa75d6b549514b722e2c50726c03e34fac4909ec3640e147ea7fa825fc8d",
            "79aa165b0c74e88ff6c3e3e027e86aad30a6957d9b7d3d8990668aafbb393ef4",
        ),
    ] {
        let bytes = std::fs::read(root.join(path)).unwrap();
        assert_eq!(format!("{:x}", Sha256::digest(&bytes)), input_hash);
        let image = olympus_raw::decode_orf(&bytes).unwrap();
        assert_eq!((image.width, image.height, image.cfa), (9280, 6932, "GRBG"));
        assert_eq!(image.active_area, olympus_raw::Rect { x: 10, y: 10, width: 9216, height: 6912 });
        let mut hash = Sha256::new();
        for chunk in image.samples.chunks(8192) {
            let bytes: Vec<u8> = chunk.iter().flat_map(|v| v.to_le_bytes()).collect();
            hash.update(bytes);
        }
        assert_eq!(format!("{:x}", hash.finalize()), sensor_hash, "{path}");
    }
    eprintln!("Matched both complete 64,328,960-sample padded rasters.");
}
