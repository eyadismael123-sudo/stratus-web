import type { Metadata } from "next";
import BlogHeader from "@/components/pages/blog/BlogHeader";
import BlogGrid from "@/components/pages/blog/BlogGrid";

export const metadata: Metadata = {
  title: "Blog — Stratus",
  description:
    "Stories on AI automation, business, and building in public.",
};

export default function BlogPage() {
  return (
    <>
      <BlogHeader />
      <BlogGrid />
    </>
  );
}
