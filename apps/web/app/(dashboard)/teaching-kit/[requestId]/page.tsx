import { TeachingKitResult } from "@/components/teaching-kit/TeachingKitResult";

export default async function TeachingKitPage({
  params,
}: {
  params: Promise<{ requestId: string }>;
}) {
  const { requestId } = await params;
  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6">
      <TeachingKitResult requestId={requestId} />
    </main>
  );
}
