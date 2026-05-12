import { useState } from 'react'

export function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const handleSubmit = () => {
    setLoading(true)
    setTimeout(() => {
      console.log('token: mock-token', { username, isLogin })
      setLoading(false)
    }, 1000)
  }
  return (
    <div className='min-h-screen bg-gray-100 flex items-center justify-center p-4'>
      <div className='bg-white rounded-xl shadow-lg p-8 w-full max-w-sm'>
        <h1 className='text-2xl font-bold text-center text-gray-800 mb-6'>{isLogin ? '登录' : '注册'}</h1>
        <div className='space-y-4'>
          <input type='text' placeholder='用户名' value={username} onChange={e => setUsername(e.target.value)}
            className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-400 focus:outline-none' />
          <input type='password' placeholder='密码' value={password} onChange={e => setPassword(e.target.value)}
            className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-400 focus:outline-none' />
          <button onClick={handleSubmit} disabled={loading || !username || !password}
            className='w-full py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 transition'>
            {loading ? '处理中...' : (isLogin ? '登录' : '注册')}
          </button>
        </div>
        <p className='text-center text-sm text-gray-500 mt-6'>
          {isLogin ? <>没有账号？<button onClick={() => setIsLogin(false)} className='text-red-500 ml-1 hover:underline'>注册</button></>
            : <>已有账号？<button onClick={() => setIsLogin(true)} className='text-red-500 ml-1 hover:underline'>登录</button></>}
        </p>
      </div>
    </div>
  )
}
