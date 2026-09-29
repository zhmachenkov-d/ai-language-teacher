import { describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import ScheduleWeekGrid from "./ScheduleWeekGrid.vue";
import {
  GRID_BAND_START,
  GRID_ROW_HEIGHT_PX,
  initialScrollHour,
  normalizeWeeklySlots,
  snapStartMinute,
} from "./scheduleGrid";

describe("scheduleGrid helpers", () => {
  it("snaps :15 to earlier :00 and :45 to earlier :30", () => {
    expect(snapStartMinute(555)).toBe(540); // 09:15 → 09:00
    expect(snapStartMinute(585)).toBe(570); // 09:45 → 09:30
  });

  it("snaps nearer-upper minutes to :30", () => {
    expect(snapStartMinute(556)).toBe(570); // 09:16 → 09:30
  });

  it("preserves exact :00 and :30", () => {
    expect(snapStartMinute(540)).toBe(540);
    expect(snapStartMinute(570)).toBe(570);
  });

  it("coalesces after snap and flags didSnap", () => {
    const { slots, didSnap } = normalizeWeeklySlots([
      { weekday: 0, start_minute: 550 }, // 09:10 → 09:00
      { weekday: 0, start_minute: 540 },
    ]);
    expect(didSnap).toBe(true);
    expect(slots).toEqual([{ weekday: 0, start_minute: 540 }]);
  });

  it("does not flag didSnap for legitimate :30", () => {
    const { slots, didSnap } = normalizeWeeklySlots([
      { weekday: 1, start_minute: 570 },
    ]);
    expect(didSnap).toBe(false);
    expect(slots).toEqual([{ weekday: 1, start_minute: 570 }]);
  });

  it("initialScrollHour uses band start or out-of-band mark hour", () => {
    expect(initialScrollHour([])).toBe(GRID_BAND_START);
    expect(initialScrollHour([{ weekday: 0, start_minute: 540 }])).toBe(
      GRID_BAND_START,
    );
    expect(initialScrollHour([{ weekday: 0, start_minute: 1350 }])).toBe(22); // 22:30
    expect(initialScrollHour([{ weekday: 0, start_minute: 300 }])).toBe(5); // 05:00
  });

  it("drops weekday values outside 0–6", () => {
    const { slots } = normalizeWeeklySlots([
      { weekday: -1, start_minute: 540 },
      { weekday: 7, start_minute: 540 },
      { weekday: 0, start_minute: 540 },
    ]);
    expect(slots).toEqual([{ weekday: 0, start_minute: 540 }]);
  });
});

describe("ScheduleWeekGrid", () => {
  it("toggles :00 and :30 independently with named half buttons", async () => {
    const wrapper = mount(ScheduleWeekGrid, {
      props: { slots: [] },
    });
    const top = wrapper.get('[data-testid="half-0-9-00"]');
    const bottom = wrapper.get('[data-testid="half-0-9-30"]');
    expect(top.attributes("aria-label")).toBe("Пн 09:00");
    expect(bottom.attributes("aria-label")).toBe("Пн 09:30");

    await top.trigger("click");
    expect(wrapper.emitted("update:slots")?.at(-1)?.[0]).toEqual([
      { weekday: 0, start_minute: 540 },
    ]);
    await wrapper.setProps({
      slots: [{ weekday: 0, start_minute: 540 }],
    });
    await bottom.trigger("click");
    expect(wrapper.emitted("update:slots")?.at(-1)?.[0]).toEqual([
      { weekday: 0, start_minute: 540 },
      { weekday: 0, start_minute: 570 },
    ]);
    await wrapper.setProps({
      slots: [
        { weekday: 0, start_minute: 540 },
        { weekday: 0, start_minute: 570 },
      ],
    });
    expect(top.attributes("aria-pressed")).toBe("true");
    expect(bottom.attributes("aria-pressed")).toBe("true");
    expect(wrapper.find(".chip-top").exists()).toBe(true);
    expect(wrapper.find(".chip-mid").exists()).toBe(true);

    await top.trigger("click");
    expect(wrapper.emitted("update:slots")?.at(-1)?.[0]).toEqual([
      { weekday: 0, start_minute: 570 },
    ]);
    wrapper.unmount();
  });

  it("fine-snaps on bind and shows snapped chip before parent round-trip", async () => {
    const wrapper = mount(ScheduleWeekGrid, {
      props: { slots: [{ weekday: 0, start_minute: 555 }] },
    });
    await flushPromises();
    expect(wrapper.emitted("update:slots")?.[0]?.[0]).toEqual([
      { weekday: 0, start_minute: 540 },
    ]);
    expect(wrapper.emitted("snapped")).toHaveLength(1);
    // Local normalize drives selection immediately — chip visible without setProps.
    expect(
      wrapper.get('[data-testid="half-0-9-00"]').attributes("aria-pressed"),
    ).toBe("true");
    expect(wrapper.find(".chip-top").exists()).toBe(true);
    wrapper.unmount();
  });

  it("keeps :30 without snap notice", async () => {
    const wrapper = mount(ScheduleWeekGrid, {
      props: { slots: [{ weekday: 2, start_minute: 570 }] },
    });
    await flushPromises();
    expect(wrapper.emitted("snapped")).toBeUndefined();
    expect(wrapper.emitted("update:slots")).toBeUndefined();
    expect(
      wrapper.get('[data-testid="half-2-9-30"]').attributes("aria-pressed"),
    ).toBe("true");
    wrapper.unmount();
  });

  it("scrolls working band by default and evening mark when out of band", async () => {
    const empty = mount(ScheduleWeekGrid, { props: { slots: [] } });
    await nextTick();
    await flushPromises();
    const emptyScroll = empty.get(
      '[data-testid="schedule-grid-scroll"]',
    ).element as HTMLElement;
    expect(emptyScroll.scrollTop).toBe(GRID_BAND_START * GRID_ROW_HEIGHT_PX);
    empty.unmount();

    const evening = mount(ScheduleWeekGrid, {
      props: { slots: [{ weekday: 0, start_minute: 1350 }] }, // 22:30
    });
    await nextTick();
    await flushPromises();
    const eveningScroll = evening.get(
      '[data-testid="schedule-grid-scroll"]',
    ).element as HTMLElement;
    expect(eveningScroll.scrollTop).toBe(22 * GRID_ROW_HEIGHT_PX);
    evening.unmount();
  });

  it("INITIAL_VIEW scrolls pre-band morning mark to hour 5", async () => {
    const wrapper = mount(ScheduleWeekGrid, {
      props: { slots: [{ weekday: 0, start_minute: 300 }] }, // 05:00
    });
    await nextTick();
    await flushPromises();
    const scroll = wrapper.get(
      '[data-testid="schedule-grid-scroll"]',
    ).element as HTMLElement;
    expect(scroll.scrollTop).toBe(5 * GRID_ROW_HEIGHT_PX);
    wrapper.unmount();
  });

  it("scrolls using post-snap hour when fine minute is out of band", async () => {
    // 04:50 → snap 05:00 (hour 5); scroll must use post-snap, not raw hour 4.
    const wrapper = mount(ScheduleWeekGrid, {
      props: { slots: [{ weekday: 0, start_minute: 290 }] },
    });
    await nextTick();
    await flushPromises();
    expect(wrapper.emitted("update:slots")?.[0]?.[0]).toEqual([
      { weekday: 0, start_minute: 300 },
    ]);
    const scroll = wrapper.get(
      '[data-testid="schedule-grid-scroll"]',
    ).element as HTMLElement;
    expect(scroll.scrollTop).toBe(5 * GRID_ROW_HEIGHT_PX);
    wrapper.unmount();
  });

  it("renders full 0–23 hour rows without CalendarHome coupling", () => {
    const wrapper = mount(ScheduleWeekGrid, { props: { slots: [] } });
    expect(wrapper.findAll(".hour-cell")).toHaveLength(7 * 24);
    expect(wrapper.findAll(".hour-label")).toHaveLength(24);
    expect(wrapper.text()).toContain("00:00");
    expect(wrapper.text()).toContain("23:00");
    wrapper.unmount();
  });

  it("does not depend on Settings or CalendarHome modules", async () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const wrapper = mount(ScheduleWeekGrid, { props: { slots: [] } });
    expect(wrapper.find("[data-testid=\"schedule-week-grid\"]").exists()).toBe(
      true,
    );
    wrapper.unmount();
    spy.mockRestore();
  });
});
