// talanta-bridge/1. Binary channels contain little-endian IEEE-754 float32 values.
// offset counts bytes. length counts scalar values. components counts values per item.
// Animated channels use frame-major, then item-major, then component order.
// PPL-02 channels are static: seat-major, then component order, stored once.
// occupancy_order stores ranked seat indices. selected_seats stores drawn seat indices.
// Float32 stores the current seat indices exactly (56,972 seats, below 2**24).
// Frame n samples start_s+n/fps. duration_s is half-open: frame_count=ceil(duration_s*fps).
// RGB is linear. Visibility is separate, including facade rest after the last cue.
export const SCHEMA = 'talanta-bridge/1';
export function packChannels(entries) {
  let offset = 0;
  const channels = entries.map(({ name, components, values }) => {
    const channel = { name, components, dtype: 'float32', offset, length: values.length };
    offset += values.length * 4; return channel;
  });
  const bytes = new Uint8Array(offset), view = new DataView(bytes.buffer);
  entries.forEach(({ values }, i) => values.forEach((v, j) => {
    if (!Number.isFinite(v)) throw new Error(`Non-finite channel value: ${entries[i].name}`);
    view.setFloat32(channels[i].offset + j * 4, v, true);
  }));
  return { channels, bytes };
}
export function unpackChannel(bytes, channel) {
  if (channel.dtype !== 'float32' || channel.offset % 4 || channel.offset < 0 || channel.length < 0 || channel.offset + channel.length * 4 > bytes.byteLength) throw new Error('Invalid channel bounds');
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  return Array.from({ length: channel.length }, (_, i) => view.getFloat32(channel.offset + i * 4, true));
}
