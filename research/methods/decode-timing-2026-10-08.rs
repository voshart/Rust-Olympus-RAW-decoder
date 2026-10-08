#![forbid(unsafe_code)]
#![deny(clippy::unwrap_used, clippy::expect_used, clippy::panic, clippy::unimplemented, clippy::todo, clippy::unreachable)]

use std::fs::File;
use std::io::Read;
use std::time::Instant;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = std::env::args_os().nth(1).ok_or("expected a raw input")?;
    let mut bytes = Vec::new();
    File::open(&path)?.take(512 * 1024 * 1024 + 1).read_to_end(&mut bytes)?;
    if bytes.len() > 512 * 1024 * 1024 {
        return Err("input exceeds 512 MiB".into());
    }
    let warmup = lightcraft_raw::decode(&bytes)?;
    let (width, height, bits) = (warmup.width, warmup.height, warmup.bits);
    let n = width.checked_mul(height).ok_or("sensor dimensions overflow")?;
    drop(warmup);
    let mut timings = Vec::new();
    for _ in 0..5 {
        let start = Instant::now();
        let raw = lightcraft_raw::decode(&bytes)?;
        timings.push(start.elapsed().as_secs_f64() * 1000.0);
        if (raw.width, raw.height, raw.bits) != (width, height, bits) || raw.data.len() != n {
            return Err("inconsistent sensor result".into());
        }
        std::hint::black_box(&raw.data);
        drop(raw);
    }
    timings.sort_by(f64::total_cmp);
    let median = *timings.get(2).ok_or("missing timings")?;
    let mp = n as f64 / 1_000_000.0;
    println!("{{\"width\":{width},\"height\":{height},\"bits\":{bits},\"megapixels\":{mp},\"file_bytes\":{},\"median_ms\":{median},\"ms_per_mp\":{},\"sorted_ms\":{timings:?}}}", bytes.len(), median / mp);
    Ok(())
}
