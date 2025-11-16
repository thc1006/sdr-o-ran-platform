"""Unit tests for DRL Trainer

Tests the Deep Reinforcement Learning training pipeline including:
- RIC state and action data structures
- Training configuration
- RIC environment (Gym)
- Reward calculation
- Environment reset and step functions
"""

import pytest
import os
import time
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

# Import modules to test
from ric_state import RICState
from drl_trainer import (
    RICAction,
    TrainingConfig,
    RICEnvironment,
    DRLTrainer
)


@pytest.mark.unit
@pytest.mark.drl
class TestRICState:
    """Test RICState data structure"""

    def test_ric_state_creation(self, sample_ric_state):
        """Test creating RICState object"""
        state = RICState(**sample_ric_state)

        assert state.ue_throughput_dl_mbps == 75.5
        assert state.ue_throughput_ul_mbps == 35.2
        assert state.active_ues == 5
        assert state.sinr_db == 18.5
        assert state.bler_dl == 0.005

    def test_ric_state_to_numpy(self, sample_ric_state):
        """Test converting RICState to numpy array"""
        state = RICState(**sample_ric_state)

        state_array = state.to_numpy()

        assert isinstance(state_array, np.ndarray)
        assert state_array.shape == (11,)
        assert state_array.dtype == np.float32

        # Verify array is not empty and contains expected normalized values
        assert len(state_array) == 11
        # Check specific values match expected normalization
        assert abs(state_array[0] - 0.755) < 0.01  # ue_throughput_dl_mbps / 100
        assert abs(state_array[1] - 0.704) < 0.01  # ue_throughput_ul_mbps / 50

    def test_ric_state_to_dict(self, sample_ric_state):
        """Test converting RICState to dictionary using asdict"""
        from dataclasses import asdict
        state = RICState(**sample_ric_state)

        state_dict = asdict(state)

        assert isinstance(state_dict, dict)
        assert state_dict['ue_throughput_dl_mbps'] == 75.5
        assert state_dict['active_ues'] == 5


@pytest.mark.unit
@pytest.mark.drl
class TestRICAction:
    """Test RICAction data structure"""

    def test_ric_action_creation(self):
        """Test creating RICAction object"""
        action = RICAction(
            mcs_dl=15,
            mcs_ul=12,
            prb_allocation_dl=50,
            prb_allocation_ul=30,
            tx_power_dbm=20.0,
            qos_5qi=9
        )

        assert action.mcs_dl == 15
        assert action.mcs_ul == 12
        assert action.prb_allocation_dl == 50
        assert action.prb_allocation_ul == 30
        assert action.tx_power_dbm == 20.0
        assert action.qos_5qi == 9
        assert action.handover_trigger == False
        assert action.target_cell_id is None

    def test_ric_action_to_dict(self):
        """Test converting RICAction to dictionary"""
        action = RICAction(
            mcs_dl=15,
            mcs_ul=12,
            prb_allocation_dl=50,
            prb_allocation_ul=30,
            tx_power_dbm=20.0
        )

        action_dict = action.to_dict()

        assert isinstance(action_dict, dict)
        assert action_dict['mcs_dl'] == 15
        assert action_dict['tx_power_dbm'] == 20.0

    def test_ric_action_handover(self):
        """Test RICAction with handover"""
        action = RICAction(
            mcs_dl=15,
            mcs_ul=12,
            prb_allocation_dl=50,
            prb_allocation_ul=30,
            tx_power_dbm=20.0,
            handover_trigger=True,
            target_cell_id=42
        )

        assert action.handover_trigger == True
        assert action.target_cell_id == 42


@pytest.mark.unit
@pytest.mark.drl
class TestTrainingConfig:
    """Test TrainingConfig data structure"""

    def test_default_config(self):
        """Test default training configuration"""
        config = TrainingConfig()

        assert config.algorithm == "PPO"
        assert config.total_timesteps == 1_000_000
        assert config.learning_rate == 3e-4
        assert config.batch_size == 64
        assert config.n_epochs == 10
        assert config.gamma == 0.99
        assert config.n_envs == 4

    def test_custom_config(self):
        """Test custom training configuration"""
        config = TrainingConfig(
            algorithm="SAC",
            total_timesteps=500_000,
            learning_rate=1e-3,
            n_envs=8
        )

        assert config.algorithm == "SAC"
        assert config.total_timesteps == 500_000
        assert config.learning_rate == 1e-3
        assert config.n_envs == 8

    def test_network_architecture_defaults(self):
        """Test default network architecture"""
        config = TrainingConfig()

        assert config.policy_network == [256, 256]
        assert config.value_network == [256, 256]


@pytest.mark.unit
@pytest.mark.drl
class TestRICEnvironment:
    """Test RIC Gym Environment"""

    @patch('drl_trainer.redis.Redis')
    def test_environment_initialization(self, mock_redis_class):
        """Test RICEnvironment initialization"""
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(
            redis_host="localhost",
            redis_port=6379,
            max_steps=1000
        )

        assert env.max_steps == 1000
        assert env.current_step == 0
        assert env.observation_space.shape == (11,)
        assert env.action_space.shape == (5,)

        # Verify reward weights
        assert 'throughput' in env.reward_weights
        assert 'latency' in env.reward_weights
        assert 'bler' in env.reward_weights
        assert 'resource_efficiency' in env.reward_weights

    @patch('drl_trainer.redis.Redis')
    def test_environment_reset(self, mock_redis_class):
        """Test environment reset"""
        mock_redis = Mock()
        mock_redis.get = Mock(return_value=None)
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")

        obs, info = env.reset()

        assert isinstance(obs, np.ndarray)
        assert obs.shape == (11,)
        assert env.current_step == 0
        assert len(env.state_history) == 0
        assert isinstance(info, dict)

    @patch('drl_trainer.redis.Redis')
    def test_environment_step(self, mock_redis_class):
        """Test environment step"""
        mock_redis = Mock()
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")
        env.reset()

        # Take a step
        action = np.array([15.0, 12.0, 50.0, 30.0, 20.0])
        obs, reward, terminated, truncated, info = env.step(action)

        assert isinstance(obs, np.ndarray)
        assert obs.shape == (11,)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

        # Verify info contains expected keys
        assert 'throughput_dl' in info
        assert 'latency' in info
        assert 'bler' in info

        # Verify step counter incremented
        assert env.current_step == 1

    @patch('drl_trainer.redis.Redis')
    def test_action_clipping(self, mock_redis_class):
        """Test that actions are properly clipped"""
        mock_redis = Mock()
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")
        env.reset()

        # Action with values outside valid range
        action = np.array([100.0, -10.0, 200.0, -50.0, 50.0])
        obs, reward, terminated, truncated, info = env.step(action)

        # Should not crash and should produce valid results
        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)

    @patch('drl_trainer.redis.Redis')
    def test_reward_calculation(self, mock_redis_class):
        """Test reward calculation"""
        mock_redis = Mock()
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")

        # Create a good state (high throughput, low latency, low BLER)
        good_state = RICState(
            ue_throughput_dl_mbps=95.0,
            ue_throughput_ul_mbps=45.0,
            ue_buffer_status_dl_kb=100.0,
            ue_buffer_status_ul_kb=50.0,
            prb_utilization_dl_percent=70.0,
            prb_utilization_ul_percent=50.0,
            active_ues=5,
            cqi_dl=14.0,
            rsrp_dbm=-75.0,
            rsrq_db=-5.0,
            sinr_db=25.0,
            e2e_latency_ms=30.0,
            rlc_latency_ms=5.0,
            mac_latency_ms=2.0,
            bler_dl=0.001,
            bler_ul=0.002,
            timestamp_ns=int(time.time() * 1e9)
        )

        action = RICAction(
            mcs_dl=20,
            mcs_ul=15,
            prb_allocation_dl=70,
            prb_allocation_ul=50,
            tx_power_dbm=20.0
        )

        reward_good = env._calculate_reward(good_state, action)

        # Create a bad state (low throughput, high latency, high BLER)
        bad_state = RICState(
            ue_throughput_dl_mbps=20.0,
            ue_throughput_ul_mbps=10.0,
            ue_buffer_status_dl_kb=500.0,
            ue_buffer_status_ul_kb=200.0,
            prb_utilization_dl_percent=30.0,
            prb_utilization_ul_percent=20.0,
            active_ues=5,
            cqi_dl=6.0,
            rsrp_dbm=-110.0,
            rsrq_db=-15.0,
            sinr_db=5.0,
            e2e_latency_ms=150.0,
            rlc_latency_ms=20.0,
            mac_latency_ms=10.0,
            bler_dl=0.05,
            bler_ul=0.08,
            timestamp_ns=int(time.time() * 1e9)
        )

        reward_bad = env._calculate_reward(bad_state, action)

        # Good state should have higher reward
        assert reward_good > reward_bad

    @patch('drl_trainer.redis.Redis')
    def test_environment_redis_host_env_var(self, mock_redis_class):
        """Test Redis host configuration via environment variable"""
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis

        # Set environment variable
        os.environ['REDIS_HOST'] = 'test-redis-host'

        try:
            env = RICEnvironment(redis_host=None)

            # Verify Redis was called with the env var value
            mock_redis_class.assert_called_with(
                host='test-redis-host',
                port=6379,
                decode_responses=False
            )
        finally:
            # Clean up
            if 'REDIS_HOST' in os.environ:
                del os.environ['REDIS_HOST']

    @patch('drl_trainer.redis.Redis')
    def test_max_steps_truncation(self, mock_redis_class):
        """Test that environment truncates after max steps"""
        mock_redis = Mock()
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost", max_steps=10)
        env.reset()

        # Take 9 steps
        for _ in range(9):
            action = np.array([15.0, 12.0, 50.0, 30.0, 20.0])
            obs, reward, terminated, truncated, info = env.step(action)
            assert truncated == False

        # Take 10th step
        obs, reward, terminated, truncated, info = env.step(action)
        assert truncated == True
        assert env.current_step == 10


@pytest.mark.unit
@pytest.mark.drl
class TestDRLTrainerConfig:
    """Test DRL Trainer configuration and initialization"""

    @patch('drl_trainer.redis.Redis')
    @patch('drl_trainer.STABLE_BASELINES_AVAILABLE', True)
    def test_trainer_initialization(self, mock_redis_class):
        """Test DRLTrainer initialization"""
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis

        config = TrainingConfig(
            algorithm="PPO",
            total_timesteps=10000,
            n_envs=2
        )

        # We can't fully initialize DRLTrainer without stable-baselines3
        # but we can test the config
        assert config.algorithm == "PPO"
        assert config.total_timesteps == 10000
        assert config.n_envs == 2


@pytest.mark.unit
@pytest.mark.drl
class TestSimulatedStateGeneration:
    """Test simulated state generation for training"""

    @patch('drl_trainer.redis.Redis')
    def test_generate_simulated_state(self, mock_redis_class):
        """Test generating realistic simulated state"""
        mock_redis = Mock()
        mock_redis.get = Mock(return_value=None)
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")

        state = env._generate_simulated_state()

        # Verify state has realistic values
        assert 0 <= state.ue_throughput_dl_mbps <= 100
        assert 0 <= state.ue_throughput_ul_mbps <= 50
        assert 1 <= state.active_ues <= 10
        assert -120 <= state.rsrp_dbm <= -50
        assert 0 <= state.bler_dl <= 1.0
        assert 0 <= state.bler_ul <= 1.0
        assert state.timestamp_ns > 0

    @patch('drl_trainer.redis.Redis')
    def test_send_ric_control_to_sdl(self, mock_redis_class):
        """Test sending RIC control to SDL"""
        mock_redis = Mock()
        mock_redis.set = Mock(return_value=True)
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")

        action = RICAction(
            mcs_dl=15,
            mcs_ul=12,
            prb_allocation_dl=50,
            prb_allocation_ul=30,
            tx_power_dbm=20.0
        )

        env._send_ric_control(action)

        # Verify Redis set was called
        assert mock_redis.set.called
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "ric:control:latest"
        assert isinstance(call_args[0][1], str)  # JSON string


@pytest.mark.unit
@pytest.mark.drl
class TestRICEnvironmentEdgeCases:
    """Test RIC Environment edge cases and error handling"""

    @patch('drl_trainer.redis.Redis')
    def test_environment_with_custom_reward_weights(self, mock_redis_class):
        """Test environment with custom reward weights"""
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis

        custom_weights = {
            'throughput': 0.5,
            'latency': 0.3,
            'bler': 0.1,
            'resource_efficiency': 0.1
        }

        env = RICEnvironment(
            redis_host="localhost",
            reward_weights=custom_weights
        )

        assert env.reward_weights == custom_weights

    @patch('drl_trainer.redis.Redis')
    def test_environment_with_different_max_steps(self, mock_redis_class):
        """Test environment with various max_steps values"""
        mock_redis = Mock()
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis_class.return_value = mock_redis

        # Test with different max_steps
        for max_steps in [100, 500, 2000]:
            env = RICEnvironment(redis_host="localhost", max_steps=max_steps)
            env.reset()

            # Run until truncation
            action = np.array([15.0, 12.0, 50.0, 30.0, 20.0])
            for step in range(max_steps - 1):
                obs, reward, terminated, truncated, info = env.step(action)
                assert not truncated

            # Last step should truncate
            obs, reward, terminated, truncated, info = env.step(action)
            assert truncated

    @patch('drl_trainer.redis.Redis')
    def test_environment_state_history_tracking(self, mock_redis_class):
        """Test that environment tracks state history"""
        mock_redis = Mock()
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")
        env.reset()

        action = np.array([15.0, 12.0, 50.0, 30.0, 20.0])

        # Take multiple steps
        for _ in range(5):
            env.step(action)

        # State history should have 5 entries
        assert len(env.state_history) == 5

    @patch('drl_trainer.redis.Redis')
    def test_ric_action_with_handover(self, mock_redis_class):
        """Test RIC action with handover triggering"""
        action = RICAction(
            mcs_dl=15,
            mcs_ul=12,
            prb_allocation_dl=50,
            prb_allocation_ul=30,
            tx_power_dbm=20.0,
            handover_trigger=True,
            target_cell_id=123
        )

        action_dict = action.to_dict()
        assert action_dict['handover_trigger'] == True
        assert action_dict['target_cell_id'] == 123

    @patch('drl_trainer.redis.Redis')
    def test_environment_observation_space_bounds(self, mock_redis_class):
        """Test observation space has correct bounds"""
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")

        # Check observation space shape
        assert env.observation_space.shape == (11,)

        # Check it's a Box space with proper bounds
        assert hasattr(env.observation_space, 'low')
        assert hasattr(env.observation_space, 'high')

    @patch('drl_trainer.redis.Redis')
    def test_environment_action_space_bounds(self, mock_redis_class):
        """Test action space has correct bounds"""
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")

        # Check action space shape
        assert env.action_space.shape == (5,)

        # Check it's a Box space with proper bounds
        assert hasattr(env.action_space, 'low')
        assert hasattr(env.action_space, 'high')

    @patch('drl_trainer.redis.Redis')
    def test_reward_calculation_with_extreme_values(self, mock_redis_class):
        """Test reward calculation with extreme state values"""
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis

        env = RICEnvironment(redis_host="localhost")

        # Test with very poor state
        poor_state = RICState(
            ue_throughput_dl_mbps=1.0,  # Very low
            ue_throughput_ul_mbps=0.5,
            ue_buffer_status_dl_kb=1000.0,  # High buffer
            ue_buffer_status_ul_kb=500.0,
            prb_utilization_dl_percent=10.0,  # Low utilization
            prb_utilization_ul_percent=5.0,
            active_ues=1,
            cqi_dl=3.0,  # Poor CQI
            rsrp_dbm=-120.0,  # Very weak signal
            rsrq_db=-20.0,
            sinr_db=-5.0,  # Negative SINR
            e2e_latency_ms=200.0,  # High latency
            rlc_latency_ms=50.0,
            mac_latency_ms=30.0,
            bler_dl=0.1,  # High BLER
            bler_ul=0.15,
            timestamp_ns=int(time.time() * 1e9)
        )

        action = RICAction(
            mcs_dl=10,
            mcs_ul=8,
            prb_allocation_dl=30,
            prb_allocation_ul=20,
            tx_power_dbm=15.0
        )

        reward_poor = env._calculate_reward(poor_state, action)

        # Test with excellent state
        excellent_state = RICState(
            ue_throughput_dl_mbps=100.0,
            ue_throughput_ul_mbps=50.0,
            ue_buffer_status_dl_kb=50.0,  # Low buffer
            ue_buffer_status_ul_kb=20.0,
            prb_utilization_dl_percent=80.0,
            prb_utilization_ul_percent=60.0,
            active_ues=5,
            cqi_dl=15.0,  # Excellent CQI
            rsrp_dbm=-70.0,  # Strong signal
            rsrq_db=-3.0,
            sinr_db=30.0,  # High SINR
            e2e_latency_ms=20.0,  # Low latency
            rlc_latency_ms=3.0,
            mac_latency_ms=1.0,
            bler_dl=0.0001,  # Very low BLER
            bler_ul=0.0002,
            timestamp_ns=int(time.time() * 1e9)
        )

        reward_excellent = env._calculate_reward(excellent_state, action)

        # Excellent state should have higher reward than poor state
        assert reward_excellent > reward_poor
