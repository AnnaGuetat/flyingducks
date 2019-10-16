import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
import olympe_deps as od

drone = olympe.Drone("10.202.0.1", drone_type=od.ARSDK_DEVICE_TYPE_BEBOP_2)
drone.connection()
drone(
    TakeOff()
    >> FlyingStateChanged(state="hovering", _timeout=5)
).wait()
drone(
    moveBy(10, 0, 0, 0)
    >> FlyingStateChanged(state="hovering", _timeout=5)
).wait()
drone(Landing()).wait()
drone.disconnection()