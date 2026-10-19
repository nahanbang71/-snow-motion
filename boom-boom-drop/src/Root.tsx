import { Composition } from "remotion";
import { Sample, SAMPLE_FRAMES } from "./Sample";

export const Root = () => (
  <Composition
    id="Sample"
    component={Sample}
    durationInFrames={SAMPLE_FRAMES}
    fps={30}
    width={1920}
    height={1080}
  />
);
