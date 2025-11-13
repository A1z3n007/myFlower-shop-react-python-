import Header from "./components/Header.jsx";
import Footer from "./components/Footer.jsx";
import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home.jsx";
import ProductPage from "./pages/ProductPage.jsx";
import CartPage from "./pages/CartPage.jsx";
import CheckoutPage from "./pages/CheckoutPage.jsx";
import SuccessPage from "./pages/SuccessPage.jsx";
import AddProductPage from "./pages/AddProductPage.jsx";
import OrdersPage from "./pages/OrdersPage.jsx";
import OrderDetailsPage from "./pages/OrderDetailsPage.jsx";
import FlowersBg from "./components/FlowersBg.jsx";
import ToastContainer from "./components/ToastContainer.jsx";
import AddModal from "./components/AddModal.jsx";
import CompareDrawer from "./components/CompareDrawer.jsx";
import AuthModal from "./components/AuthModal.jsx";
import ComparePage from "./pages/ComparePage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import FavoritesPage from "./pages/FavoritesPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";

export default function App() {
  return (
    <div className="app">
      <FlowersBg />
      <Header />
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/product/:id" element={<ProductPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/success" element={<SuccessPage />} />
          <Route path="/add" element={<AddProductPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/orders/:id" element={<OrderDetailsPage />} />
          <Route path="/compare" element={<ComparePage />} />

          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </main>
      <Footer />
      <ToastContainer />
      <AddModal />
      <CompareDrawer />
      <AuthModal />
    </div>
  );
}
