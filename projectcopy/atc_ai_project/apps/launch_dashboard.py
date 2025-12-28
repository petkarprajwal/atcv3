try:
	from launch_dashboard import main as _main
except Exception:
	import runpy as _runpy
	_runpy.run_module('launch_dashboard', run_name='__main__')
else:
	if __name__ == '__main__':
		_main()


