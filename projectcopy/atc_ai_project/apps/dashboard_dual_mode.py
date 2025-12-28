try:
	from dashboard_dual_mode import main as _main
except Exception:
	import runpy as _runpy
	_runpy.run_module('dashboard_dual_mode', run_name='__main__')
else:
	if __name__ == '__main__':
		_main()


