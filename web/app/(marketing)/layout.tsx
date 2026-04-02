import { Header } from "@/components/layouts/Header";
import { Footer } from "@/components/layouts/Footer";

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col min-h-screen">
      <Header variant="marketing" />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
