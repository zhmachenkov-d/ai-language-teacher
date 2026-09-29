import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import ListeningPlayer from "./ListeningPlayer.vue";

/** happy-dom audio lacks real media timing — stub duration/currentTime/play. */
function stubAudio(
  audio: HTMLAudioElement,
  opts: { duration?: number; playImpl?: () => Promise<void> } = {},
): {
  setCurrentTime: (t: number) => void;
  getCurrentTime: () => number;
} {
  let current = 0;
  const duration = opts.duration ?? 12.4;
  Object.defineProperty(audio, "duration", {
    configurable: true,
    get: () => duration,
  });
  Object.defineProperty(audio, "currentTime", {
    configurable: true,
    get: () => current,
    set: (v: number) => {
      current = v;
    },
  });
  Object.defineProperty(audio, "paused", {
    configurable: true,
    get: () => (audio as HTMLAudioElement & { _paused?: boolean })._paused !== false,
    set: (v: boolean) => {
      (audio as HTMLAudioElement & { _paused?: boolean })._paused = v;
    },
  });
  (audio as HTMLAudioElement & { _paused?: boolean })._paused = true;
  audio.play = vi.fn(async () => {
    if (opts.playImpl) {
      await opts.playImpl();
    }
    (audio as HTMLAudioElement & { _paused?: boolean })._paused = false;
    audio.dispatchEvent(new Event("play"));
  }) as unknown as HTMLAudioElement["play"];
  audio.pause = vi.fn(() => {
    (audio as HTMLAudioElement & { _paused?: boolean })._paused = true;
    audio.dispatchEvent(new Event("pause"));
  }) as unknown as HTMLAudioElement["pause"];
  return {
    setCurrentTime: (t: number) => {
      current = t;
    },
    getCurrentTime: () => current,
  };
}

async function mountReady(
  opts: { duration?: number; playImpl?: () => Promise<void> } = {},
): Promise<{
  wrapper: ReturnType<typeof mount>;
  audio: HTMLAudioElement;
  clock: ReturnType<typeof stubAudio>;
}> {
  const wrapper = mount(ListeningPlayer, {
    props: { src: "blob:fake-audio" },
  });
  const audio = wrapper.get('[data-testid="listening-audio"]')
    .element as HTMLAudioElement;
  const clock = stubAudio(audio, opts);
  await audio.dispatchEvent(new Event("loadedmetadata"));
  await nextTick();
  return { wrapper, audio, clock };
}

describe("ListeningPlayer", () => {
  it("disables scrubber and shows 0:00 / — before duration is known", () => {
    const wrapper = mount(ListeningPlayer, {
      props: { src: "blob:fake-audio" },
    });
    const scrub = wrapper.get('[data-testid="listening-scrub"]');
    expect((scrub.element as HTMLInputElement).disabled).toBe(true);
    expect(wrapper.get('[data-testid="listening-times"]').text()).toBe(
      "0:00 / —",
    );
    expect(wrapper.find('[data-testid="listening-player"]').exists()).toBe(
      true,
    );
    wrapper.unmount();
  });

  it("enables scrubber and formats times after loadedmetadata", async () => {
    const { wrapper } = await mountReady({ duration: 65.9 });
    const scrub = wrapper.get('[data-testid="listening-scrub"]');
    expect((scrub.element as HTMLInputElement).disabled).toBe(false);
    expect(scrub.attributes("aria-valuemin")).toBe("0");
    expect(Number(scrub.attributes("aria-valuemax"))).toBeCloseTo(65.9);
    expect(wrapper.get('[data-testid="listening-times"]').text()).toBe(
      "0:00 / 1:05",
    );
    expect(wrapper.get('[data-testid="listening-play"]').attributes("aria-label")).toBe(
      "Слушать",
    );
    expect(
      wrapper.get('[data-testid="listening-replay"]').attributes("aria-label"),
    ).toBe("Сначала");
    wrapper.unmount();
  });

  it("play/pause toggles and scrub seek clamps currentTime", async () => {
    const { wrapper, audio, clock } = await mountReady({ duration: 10 });

    await wrapper.get('[data-testid="listening-play"]').trigger("click");
    expect(audio.play).toHaveBeenCalled();
    await nextTick();
    expect(wrapper.get('[data-testid="listening-play"]').text()).toBe("Пауза");
    expect(
      wrapper.get('[data-testid="listening-play"]').attributes("aria-label"),
    ).toBe("Пауза");

    await wrapper.get('[data-testid="listening-play"]').trigger("click");
    expect(audio.pause).toHaveBeenCalled();
    await nextTick();
    expect(wrapper.get('[data-testid="listening-play"]').text()).toBe("Слушать");

    const scrub = wrapper.get('[data-testid="listening-scrub"]');
    await scrub.setValue(4.2);
    await scrub.trigger("input");
    expect(clock.getCurrentTime()).toBeCloseTo(4.2);
    expect(wrapper.get('[data-testid="listening-times"]').text()).toBe(
      "0:04 / 0:10",
    );

    await scrub.setValue(99);
    await scrub.trigger("input");
    expect(clock.getCurrentTime()).toBe(10);
    wrapper.unmount();
  });

  it("timeupdate advances times and scrub position", async () => {
    const { wrapper, audio, clock } = await mountReady({ duration: 10 });
    clock.setCurrentTime(3.7);
    await audio.dispatchEvent(new Event("timeupdate"));
    await nextTick();
    expect(wrapper.get('[data-testid="listening-times"]').text()).toBe(
      "0:03 / 0:10",
    );
    expect(
      Number(
        (wrapper.get('[data-testid="listening-scrub"]').element as HTMLInputElement)
          .value,
      ),
    ).toBeCloseTo(3.7);
    wrapper.unmount();
  });

  it("scrub change clears scrubbing so later timeupdate advances times", async () => {
    const { wrapper, audio, clock } = await mountReady({ duration: 10 });
    const scrub = wrapper.get('[data-testid="listening-scrub"]');
    await scrub.setValue(2);
    await scrub.trigger("input");
    expect(wrapper.get('[data-testid="listening-times"]').text()).toBe(
      "0:02 / 0:10",
    );
    await scrub.trigger("change");
    clock.setCurrentTime(6);
    await audio.dispatchEvent(new Event("timeupdate"));
    await nextTick();
    expect(wrapper.get('[data-testid="listening-times"]').text()).toBe(
      "0:06 / 0:10",
    );
    wrapper.unmount();
  });

  it("Сначала restarts from zero and keeps ended-once sticky", async () => {
    const { wrapper, audio, clock } = await mountReady({ duration: 8 });

    clock.setCurrentTime(8);
    await audio.dispatchEvent(new Event("ended"));
    await nextTick();
    expect(wrapper.emitted("ended-once")).toHaveLength(1);

    clock.setCurrentTime(5);
    await wrapper.get('[data-testid="listening-replay"]').trigger("click");
    expect(clock.getCurrentTime()).toBe(0);
    expect(audio.play).toHaveBeenCalled();
    // Sticky: no second emit after restart.
    expect(wrapper.emitted("ended-once")).toHaveLength(1);
    wrapper.unmount();
  });

  it("seek to end without native ended does not emit ended-once", async () => {
    const { wrapper, clock } = await mountReady({ duration: 5 });
    const scrub = wrapper.get('[data-testid="listening-scrub"]');
    await scrub.setValue(5);
    await scrub.trigger("input");
    expect(clock.getCurrentTime()).toBe(5);
    expect(wrapper.emitted("ended-once")).toBeUndefined();
    wrapper.unmount();
  });

  it("play() rejection emits Russian playback-error", async () => {
    const { wrapper } = await mountReady({
      duration: 3,
      playImpl: () => Promise.reject(new Error("autoplay blocked")),
    });
    await wrapper.get('[data-testid="listening-play"]').trigger("click");
    await vi.waitUntil(() =>
      (wrapper.emitted("playback-error") ?? []).some(
        ([msg]) => typeof msg === "string" && msg.includes("Не удалось воспроизвести"),
      ),
    );
    const messages = (wrapper.emitted("playback-error") ?? []).map(([msg]) => msg);
    expect(messages[0]).toBe("");
    expect(messages.at(-1)).toContain("Не удалось воспроизвести");
    wrapper.unmount();
  });
});
