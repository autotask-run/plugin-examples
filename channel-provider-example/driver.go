package loopbackchannel

import (
	"context"
	"fmt"
	"sync"

	"github.com/aak1247/autotask/internal/models"
	"github.com/aak1247/autotask/internal/services"
)

type runtimeDriverFactory struct{}

func (runtimeDriverFactory) ProviderType() string { return "loopback" }

func (runtimeDriverFactory) NewDriver(channel *models.Channel) (services.ChannelRuntimeDriver, error) {
	if channel == nil {
		return nil, fmt.Errorf("channel is required")
	}
	return &runtimeDriver{channelID: channel.ID}, nil
}

type runtimeDriver struct {
	mu        sync.Mutex
	channelID uint
	started   bool
	replies   []services.ChannelReply
}

func (r *runtimeDriver) ProviderType() string { return "loopback" }

func (r *runtimeDriver) Capabilities() models.ChannelCapabilities {
	return models.ChannelCapabilities{DirectMessage: true}
}

func (r *runtimeDriver) Start(_ context.Context, channel *models.Channel, sink services.ChannelRuntimeSink) error {
	if channel == nil || sink == nil {
		return fmt.Errorf("channel and sink are required")
	}
	r.mu.Lock()
	r.started = true
	r.mu.Unlock()
	sink.OnReady(channel.ID, map[string]interface{}{"provider": "loopback", "fixture": true})
	return nil
}

func (r *runtimeDriver) Stop(_ context.Context) error {
	r.mu.Lock()
	r.started = false
	r.mu.Unlock()
	return nil
}

func (r *runtimeDriver) Send(_ context.Context, reply services.ChannelReply) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if !r.started {
		return fmt.Errorf("loopback driver is stopped")
	}
	r.replies = append(r.replies, reply)
	return nil
}

// Replies returns a copy for a host-side test. A production adapter should
// send through its platform SDK and must not expose raw credentials here.
func (r *runtimeDriver) Replies() []services.ChannelReply {
	r.mu.Lock()
	defer r.mu.Unlock()
	return append([]services.ChannelReply(nil), r.replies...)
}
