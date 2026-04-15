import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import AIEvaluation from "./pages/AIEvaluation";
import DataQuality from "./pages/DataQuality";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

/**
 * HashRouter is used for SPA static hosting compatibility.
 * It prevents 404 errors on page refresh for nested routes
 * without requiring server-side rewrite rules.
 * Routes are accessed via /#/path instead of /path.
 */
const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <HashRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/ai-evaluation" element={<AIEvaluation />} />
          <Route path="/data-quality" element={<DataQuality />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </HashRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
