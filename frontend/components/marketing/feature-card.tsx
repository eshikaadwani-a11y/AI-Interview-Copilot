"use client";

import { motion } from "framer-motion";
import { type LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  index: number;
}

export function FeatureCard({ icon: Icon, title, description, index }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
    >
      <Card className="h-full transition-colors hover:border-primary/40">
        <CardContent className="flex flex-col gap-3 pt-6">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/15 text-primary">
            <Icon className="h-5 w-5" />
          </span>
          <h3 className="text-base font-semibold">{title}</h3>
          <p className="text-sm leading-relaxed text-muted">{description}</p>
        </CardContent>
      </Card>
    </motion.div>
  );
}
