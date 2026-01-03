import { redirect } from 'next/navigation'

export default function Home() {
  // Redirect to dashboard (which will redirect to login if not authenticated)
  redirect('/dashboard')
}
