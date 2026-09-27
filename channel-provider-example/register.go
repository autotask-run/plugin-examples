// Copy this package into an AutoTask Server checkout before compiling it.
// The imports intentionally use AutoTask's internal packages: the current
// Channel extension point is source-integrated and is not a standalone SDK.
package loopbackchannel

import (
	_ "embed"
	"strings"

	"github.com/aak1247/autotask/internal/models"
	"github.com/aak1247/autotask/internal/plugins/manifest"
	"github.com/aak1247/autotask/internal/plugins/registry"
	"github.com/aak1247/autotask/internal/services"
	"gorm.io/datatypes"
)

//go:embed autotask-plugin.json
var manifestJSON string

type provider struct{ info models.ChannelProviderInfo }

func Register(reg registry.PluginRegistry) error {
	mf, err := manifest.ParseJSON(strings.NewReader(manifestJSON))
	if err != nil {
		return err
	}
	if err := reg.RegisterPlugin(*mf); err != nil {
		return err
	}
	if err := reg.RegisterChannelRuntimeDriverFactory(runtimeDriverFactory{}); err != nil {
		return err
	}
	info, ok := mf.ChannelProviderInfo("loopback")
	if !ok {
		return services.ErrChannelInvalidType
	}
	return reg.RegisterChannelProvider(provider{info: info})
}

func (p provider) Info() models.ChannelProviderInfo { return p.info }

func (p provider) ValidateConfig(config datatypes.JSON) error {
	return services.ValidateChannelProviderConfig(p.info, config)
}

func (p provider) NormalizeExternalID(externalID string) string {
	return strings.TrimSpace(strings.ToLower(externalID))
}
