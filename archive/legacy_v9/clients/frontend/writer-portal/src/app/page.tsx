import { redirect } from 'next/navigation';

export default function HomePage() {
  // Redirect to the dashboard
  redirect('/dashboard');

  return (
    <div>Redirecting...</div>
  );
}

