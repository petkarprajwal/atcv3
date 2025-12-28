try:
	from launch_atc_system_realtime import main as _main
except Exception:
	import runpy as _runpy
	_runpy.run_module('launch_atc_system_realtime', run_name='__main__')
else:
	if __name__ == '__main__':
		_main()


