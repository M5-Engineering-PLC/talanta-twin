/** Cover a source rectangle with a viewport, in full-frame source pixels. */
export function stillFit(baseFov, viewportWidth, viewportHeight, crop = null) {
  if (![baseFov, viewportWidth, viewportHeight].every(Number.isFinite)
      || baseFov <= 0 || baseFov >= 180 || viewportWidth <= 0 || viewportHeight <= 0) {
    throw new RangeError('Invalid still projection');
  }
  const fullWidth = 1920, fullHeight = 1080;
  const source = crop ?? { x: 0, y: 0, width: fullWidth, height: fullHeight };
  const aspect = viewportWidth / viewportHeight;
  // The 607-pixel source crop was resized to a 1080 x 1920 JPEG. Retain that tiny
  // horizontal rescale instead of assuming that the crop and JPEG aspects are equal.
  const imageAspect = source.imageAspect ?? source.width / source.height;
  const height = source.height * Math.min(1, imageAspect / aspect);
  const width = source.width * Math.min(1, aspect / imageAspect);
  const x = source.x + (source.width - width) / 2, y = source.y + (source.height - height) / 2;
  const effectiveFov = 2 * Math.atan(Math.tan(baseFov * Math.PI / 360) * height / fullHeight) * 180 / Math.PI;
  // Phone crops are off-axis. Keep the full Cycles vertical FOV and let the sub-window crop it.
  const scale = viewportHeight / height;
  return { fov: crop ? baseFov : effectiveFov, effectiveFov, rect: { x, y, width, height },
    offset: crop ? { fullWidth: fullWidth * scale, fullHeight: fullHeight * scale,
      x: x * scale, y: y * scale, width: width * scale, height: height * scale } : null };
}
