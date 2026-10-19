import { Composition } from "remotion";
import { Sample, SAMPLE_FRAMES } from "./Sample";
import { NeonClip } from "./Neon";
import { ClipProps, clipFrames } from "./neonTiming";
import clips from "./clips.json";

export const Root = () => (
  <>
    <Composition
      id="Sample"
      component={Sample}
      durationInFrames={SAMPLE_FRAMES}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="Line"
      component={NeonClip}
      durationInFrames={90}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={clips[6] as ClipProps}
      calculateMetadata={({ props }) => ({ durationInFrames: clipFrames(props as ClipProps) })}
    />
  </>
);
