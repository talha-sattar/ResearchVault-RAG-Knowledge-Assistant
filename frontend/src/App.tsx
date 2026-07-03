import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Search from "./pages/Search";
import PaperDetail from "./pages/PaperDetail";
import Chat from "./pages/Chat";
import Compare from "./pages/Compare";
import Collections from "./pages/Collections";
import Preferences from "./pages/Preferences";
import History from "./pages/History";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Search />} />
        <Route path="/papers/:id" element={<PaperDetail />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/collections" element={<Collections />} />
        <Route path="/preferences" element={<Preferences />} />
        <Route path="/history" element={<History />} />
      </Route>
    </Routes>
  );
}
