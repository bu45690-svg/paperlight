import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { ThemeProvider } from "@/context/ThemeContext";
import { ToastProvider } from "@/components/ui/Toast";
import DashboardPage from "@/pages/DashboardPage";
import UploadPage from "@/pages/UploadPage";
import PaperDetailPage from "@/pages/PaperDetailPage";
import SearchPage from "@/pages/SearchPage";

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/papers/:paperId" element={<PaperDetailPage />} />
              <Route path="/search" element={<SearchPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  );
}
