export function BrandMark({ size = "md" }: { size?: "sm" | "md" }) {
  const box = size === "sm" ? "size-9" : "size-12";
  const icon = size === "sm" ? "size-4.5" : "size-6";

  return (
    <div
      className={`${box} bg-primary text-primary-foreground flex items-center justify-center rounded-xl`}
    >
      <svg viewBox="0 0 24 24" className={icon} fill="none" stroke="currentColor" strokeWidth="2.1">
        <path d="M4 19.5C4 18.12 5.12 17 6.5 17H20V4H6.5C5.12 4 4 5.12 4 6.5v13Z" />
        <path d="M8 8h8M8 11.5h8" />
      </svg>
    </div>
  );
}
