//! Write uncorrected little-endian u16 samples; never overwrite an existing file.
#![forbid(unsafe_code)]
#![deny(clippy::unwrap_used, clippy::expect_used, clippy::panic, clippy::unimplemented, clippy::todo, clippy::unreachable)]

use std::io::{Read, Write};

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args_os().skip(1);
    let input = args.next().ok_or("usage: decode input.orf output.u16le")?;
    let output = args.next().ok_or("usage: decode input.orf output.u16le")?;
    if args.next().is_some() {
        return Err("usage: decode input.orf output.u16le".into());
    }
    const LIMIT: usize = 512 * 1024 * 1024;
    let file = std::fs::File::open(&input)?;
    let len = usize::try_from(file.metadata()?.len())?;
    if len > LIMIT {
        return Err("input exceeds 512 MiB".into());
    }
    let mut bytes = Vec::new();
    bytes.try_reserve_exact(len)?;
    bytes.resize(len, 0);
    let mut reader = std::io::BufReader::new(file);
    reader.read_exact(&mut bytes)?;
    if reader.read(&mut [0])? != 0 {
        return Err("input grew while reading".into());
    }
    let image = olympus_raw::decode_orf(&bytes)?;
    let file = std::fs::OpenOptions::new().write(true).create_new(true).open(output)?;
    let mut writer = std::io::BufWriter::new(file);
    for sample in &image.samples {
        writer.write_all(&sample.to_le_bytes())?;
    }
    writer.flush()?;
    println!(
        "{}x{} bits={} cfa={} active={:?} orientation={}",
        image.width, image.height, image.bits, image.cfa, image.active_area, image.orientation
    );
    Ok(())
}

fn main() -> std::process::ExitCode {
    match run() {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{error}");
            std::process::ExitCode::FAILURE
        }
    }
}
