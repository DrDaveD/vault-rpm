# Forked from vault.spec by John Boero - jboero@hashicorp.com

Name: vault
Version: 1.6.2
Release: 1%{?dist}
Summary: Vault is a tool for securely accessing secrets
License: MPL
# download with:
# $ curl -o %{name}-rpm-%{version}.tar.gz \
#    https://codeload.github.com/fermitools/%{name}-rpm/tar.gz/v%{version}
Source0: %{name}-rpm-%{version}.tar.gz
# This is created by ./make-source-tarball
Source1: %{name}-src-%{version}.tar.gz

BuildRequires: golang
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
URL: https://www.vaultproject.io/

# This is to avoid
#   *** ERROR: No build ID note found
%define debug_package %{nil}

%description
Vault secures, stores, and tightly controls access to tokens, passwords,
certificates, API keys, and other secrets in modern computing. Vault handles
leasing, key revocation, key rolling, and auditing. Through a unified API, users
can access an encrypted Key/Value store and network encryption-as-a-service, or
generate AWS IAM/STS credentials, SQL/NoSQL databases, X.509 certificates, SSH
credentials, and more.

%prep
%setup -q -n %{name}-rpm-%{version}
RPMDIR=`pwd`
%setup -q -T -b 1 -n %{name}-src-%{version}
%if 0%{?el8}
cd %{name}-%{version}
patch -p1 <$RPMDIR/centos83mingo.patch
cd ..
%endif

%build
# starts out in %{name}-src-%{version} directory
export GOPATH="`pwd`/gopath"
export PATH=$GOPATH/bin:$PATH
export GOPROXY=file://$(go env GOMODCACHE)/cache/download
cd %{name}-%{version}
# this prevents the build from trying to use git to figure out the version
#  which fails because there's no git info
ln -s /bin/true $GOPATH/bin/git
make dev-ui

%install
# starts out in %{name}-src-%{version} directory
mkdir -p %{buildroot}%{_bindir}/
cp -p %{name}-%{version}/bin/%{name} %{buildroot}%{_bindir}/

cd ../%{name}-rpm-%{version}
mkdir -p %{buildroot}%{_sysconfdir}/%{name}.d
cp -p vault.hcl %{buildroot}%{_sysconfdir}/%{name}.d

mkdir -p %{buildroot}%{_sharedstatedir}/%{name}

mkdir -p %{buildroot}/usr/lib/systemd/system/
cp -p vault.service %{buildroot}/usr/lib/systemd/system/

%clean
rm -rf %{buildroot}
rm -rf %{_builddir}/%{name}-*-%{version}

%files
%{_bindir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}.d/%{name}.hcl
%attr(0750,%{name},%{name}) %dir %{_sharedstatedir}/%{name}
/usr/lib/systemd/system/%{name}.service

%pre
getent group %{name} > /dev/null || groupadd -r %{name}
getent passwd %{name} > /dev/null || \
    useradd -r -d %{_sharedstatedir}/%{name} -g %{name} \
    -s /sbin/nologin -c "Vault secret management tool" %{name}
exit 0

%post
/usr/bin/systemctl daemon-reload
%systemd_post %{name}.service
/sbin/setcap cap_ipc_lock=+ep %{_bindir}/%{name}

%preun
%systemd_preun %{name}.service
if [ $1 -eq 0 ]; then
      /usr/bin/systemctl --no-reload disable %{name}.service
      /usr/bin/systemctl stop %{name}.service >/dev/null 2>&1 ||:
      /usr/bin/systemctl disable %{name}.service

    fi
    if [ $1 -eq 1 ]; then
      /usr/bin/systemctl --no-reload disable %{name}.service
      /usr/bin/systemctl stop %{name}.service
    fi
    
%postun
%systemd_postun_with_restart %{name}.service

%changelog
* Wed Feb 17 2021 Dave Dykstra <dwd@fnal.gov> 1.6.2-1
- Initial build
