import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function LoginPage() {
  return (
    <main className="bg-mesh flex min-h-screen items-center justify-center px-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            Authentication arrives in Milestone 2. This route is scaffolded as
            part of the foundation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/" className="text-sm text-primary hover:underline">
            ← Back home
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
