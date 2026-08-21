import "@testing-library/jest-dom";

// Silence Next.js router warnings in jsdom
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
  redirect: vi.fn(),
}));

// Silence Next.js Link / Image imports that require the Next.js runtime
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    [k: string]: unknown;
  }) => {
    const React = require("react");
    return React.createElement("a", { href, ...rest }, children);
  },
}));

vi.mock("next/image", () => ({
  default: (props: Record<string, unknown>) => {
    const React = require("react");
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return React.createElement("img", props);
  },
}));
