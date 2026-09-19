export function replayFrameIndex(
  frames: Array<{ t: number }>,
  replayTime: number,
): number {
  if (frames.length === 0) return -1
  let result = 0
  for (let index = 0; index < frames.length; index += 1) {
    if (frames[index].t <= replayTime) result = index
    else break
  }
  return result
}
